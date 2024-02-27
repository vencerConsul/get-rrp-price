import csv

def process_sku_rrp(csv_sku_path, csv_products_path, output_csv_path):
    try:
        sku_rrp_data = []

        with open(csv_sku_path, 'r') as sku_file:
            sku_reader = csv.reader(sku_file)
            next(sku_reader)

            for sku_row in sku_reader:
                sku_value = sku_row[0]

                with open(csv_products_path, 'r') as products_file:
                    products_reader = csv.DictReader(products_file)

                    for product_row in products_reader:
                        if sku_value == product_row['code']:
                            rrp_value = product_row['rrp']
                            sku_rrp_data.append({'SKU': sku_value, 'RRP': rrp_value})
                            break

        with open(output_csv_path, 'w', newline='') as output_file:
            fieldnames = ['SKU', 'RRP']
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(sku_rrp_data)

        print(f"Process completed. Results saved to: {output_csv_path}")

    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
    except Exception as e:
        print(f"Error: {e}")

sku_csv = 'sku.csv' # csv file exported from officesuppy products that has column of SKU
products_csv = 'products.csv' # catalogue csv file (I just rename the file)
output_csv_path = 'output.csv' # output

process_sku_rrp(sku_csv, products_csv, output_csv_path)
