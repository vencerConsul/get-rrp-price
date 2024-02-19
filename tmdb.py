import csv
import requests
import time
from datetime import datetime

def fetch_movie_details(api_key, page):
    url = f'https://api.themoviedb.org/3/movie/popular'
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'page': page
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data['results']

def get_movie_details(movie_id, api_key):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'append_to_response': 'videos,release_dates'
    }

    response = requests.get(url, params=params)
    data = response.json()

    user_score = data['vote_count'] if 'vote_count' in data else 'N/A'

    if not user_score or (user_score and int(user_score) < 500):
        return None  # Skip the movie if score less than 500

    rating = data['vote_average'] if 'vote_average' in data else 'N/A'

    if rating and float(rating) < 7:
        return None  # Skip the movie if the rating is less than 7

    movieID = data['id']
    title = data['title']
    year = data['release_date'][:4] if 'release_date' in data else 'N/A'
    rating = data['vote_average'] if 'vote_average' in data else 'N/A'
    user_score = data['vote_count'] if 'vote_count' in data else 'N/A'
    release_date = data['release_date']
    movie_status = data['status'] if 'status' in data else 'N/A'
    genres = ', '.join(genre['name'] for genre in data['genres']) if 'genres' in data else 'N/A'
    runtime = f"{data['runtime'] // 60}h {data['runtime'] % 60}m" if 'runtime' in data and data['runtime'] else 'N/A'
    overview = data['overview'] if 'overview' in data else 'N/A'
    
    poster_path = data['poster_path'] if 'poster_path' in data else 'N/A'
    poster_url = f'https://image.tmdb.org/t/p/w500/{poster_path}' if poster_path else 'N/A'

    trailer_key = data['videos']['results'][0]['key'] if 'videos' in data and 'results' in data['videos'] and data['videos']['results'] else 'N/A'
    trailer_url = f'https://www.youtube.com/watch?v={trailer_key}' if trailer_key else 'N/A'

    certification = get_movie_certification(data)

    return {
        'Movie ID': movieID,
        'Title': title,
        'Year': year,
        'Rating': rating,
        'User Score': user_score,
        'Release Date': release_date,
        'Genres': genres,
        'Runtime': runtime,
        'Overview': overview,
        'Poster Image': poster_url,
        'Trailer URL': trailer_url,
        'Movie Status': movie_status,
        'Certification': certification
    }

def get_movie_certification(data):
    release_dates = data.get('release_dates', {}).get('results', [])
    
    for release in release_dates:
        if release.get('iso_3166_1') == 'US':
            certifications = release.get('release_dates', [])
            for certification_info in certifications:
                certification = certification_info.get('certification', 'N/A')
                if certification:
                    return certification
    
    return 'N/A'

def movie_id_exists(movie_id, file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        existing_ids = {row['Movie ID'] for row in reader}
        return movie_id in existing_ids

def write_to_csv(movie_details, file_path):
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        fieldnames = ['Movie ID', 'Title', 'Year', 'Rating', 'User Score', 'Release Date', 'Genres', 'Runtime', 'Overview', 'Poster Image', 'Trailer URL', 'Movie Status', 'Certification']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if file.tell() == 0:
            writer.writeheader()

        for movie in movie_details:
            movie_id = movie['Movie ID']
            
            if not movie_id_exists(movie_id, file_path):
                writer.writerow(movie)

def main(api_key, batch_size=20):
    total_movies = 200000
    movies_per_page = 20
    total_pages = total_movies // movies_per_page

    for batch_start in range(1, total_pages + 1, batch_size):
        batch_end = min(batch_start + batch_size, total_pages + 1)
        all_movie_details = []

        print(f"Processing Batch {batch_start}-{batch_end - 1}")

        for page in range(batch_start, batch_end):
            movie_list = fetch_movie_details(api_key, page)

            for movie in movie_list:
                movie_id = movie['id']
                movie_details = get_movie_details(movie_id, api_key)

                if movie_details:
                    all_movie_details.append(movie_details)

        write_to_csv(all_movie_details, 'movie_details.csv')
        
        time.sleep(2)

if __name__ == "__main__":
    api_key = 'api_key_here'
    main(api_key)