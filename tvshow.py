import csv
import requests
import time
from datetime import datetime

def fetch_tv_show_details(api_key, page):
    url = f'https://api.themoviedb.org/3/tv/popular'
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'page': page
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data['results']

def get_tv_show_details(tv_show_id, api_key):
    url = f'https://api.themoviedb.org/3/tv/{tv_show_id}'
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'append_to_response': 'videos,release_dates'
    }

    response = requests.get(url, params=params)
    data = response.json()

    user_score = data['vote_count'] if 'vote_count' in data else 'N/A'

    if not user_score or (user_score and int(user_score) < 500):
        return None  # Skip the TV show if score is less than 500

    rating = data['vote_average'] if 'vote_average' in data else 'N/A'

    if rating and float(rating) < 7:
        return None  # Skip TV show if the rating is less than 7

    tv_show_id = data['id']
    name = data['name']
    first_air_date = data['first_air_date']
    genres = ', '.join(genre['name'] for genre in data['genres']) if 'genres' in data else 'N/A'
    episode_runtime = f"{data['episode_run_time'][0] // 60}h {data['episode_run_time'][0] % 60}m" if 'episode_run_time' in data and data['episode_run_time'] else 'N/A'
    overview = data['overview'] if 'overview' in data else 'N/A'
    
    poster_path = data['poster_path'] if 'poster_path' in data else 'N/A'
    poster_url = f'https://image.tmdb.org/t/p/w500/{poster_path}' if poster_path else 'N/A'

    trailer_key = data['videos']['results'][0]['key'] if 'videos' in data and 'results' in data['videos'] and data['videos']['results'] else 'N/A'
    trailer_url = f'https://www.youtube.com/watch?v={trailer_key}' if trailer_key else 'N/A'

    certification = get_tv_show_certification(data)

    return {
        'TV Show ID': tv_show_id,
        'Name': name,
        'First Air Date': first_air_date,
        'Rating': rating,
        'User Score': user_score,
        'Genres': genres,
        'Episode Runtime': episode_runtime,
        'Overview': overview,
        'Poster Image': poster_url,
        'Trailer URL': trailer_url,
        'Certification': certification
    }

def get_tv_show_certification(data):
    release_dates = data.get('content_ratings', {}).get('results', [])
    
    for release in release_dates:
        if release.get('iso_3166_1') == 'US': 
            certification = release.get('rating', 'N/A')
            if certification:
                return certification
    
    return 'N/A'

def tv_show_id_exists(tv_show_id, file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        existing_ids = {row['TV Show ID'] for row in reader}
        return tv_show_id in existing_ids

def write_to_csv(tv_show_details, file_path):
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        fieldnames = ['TV Show ID', 'Name', 'First Air Date', 'Rating', 'User Score', 'Genres', 'Episode Runtime', 'Overview', 'Poster Image', 'Trailer URL', 'Certification']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if file.tell() == 0:
            writer.writeheader()

        for tv_show in tv_show_details:
            tv_show_id = tv_show['TV Show ID']
            
            if not tv_show_id_exists(tv_show_id, file_path):
                writer.writerow(tv_show)

def main(api_key, batch_size=20):
    total_tv_shows = 200000
    tv_shows_per_page = 20
    total_pages = total_tv_shows // tv_shows_per_page

    for batch_start in range(1, total_pages + 1, batch_size):
        batch_end = min(batch_start + batch_size, total_pages + 1)
        all_tv_show_details = []

        print(f"Processing Batch {batch_start}-{batch_end - 1}")

        for page in range(batch_start, batch_end):
            tv_show_list = fetch_tv_show_details(api_key, page)

            for tv_show in tv_show_list:
                tv_show_id = tv_show['id']
                tv_show_details = get_tv_show_details(tv_show_id, api_key)

                if tv_show_details:
                    all_tv_show_details.append(tv_show_details)

        write_to_csv(all_tv_show_details, 'tv_show_details.csv')
        
        time.sleep(2)

if __name__ == "__main__":
    api_key = 'api_key_here'
    main(api_key)