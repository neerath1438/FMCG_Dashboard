import pandas as pd
import random

def generate_realistic_mock_data(filename="sample_fmcg_data.xlsx"):
    """
    Generate mock FMCG data matching the real data structure from MongoDB.
    Structure matches: Markets, Product Segment, MANUFACTURER, MPACK, NRMSIZE, 
    BRAND, ITEM, UPC, VARIANT, Facts, monthly columns (w/e dates), MAT
    """
    
    # Sample brands and products
    brands_products = {
        "POCKY": [
            ("GLICO BRAND POCKY STRAWBERRY 38GM", "STRAWBERRY", "0000052868788"),
            ("GLICO BRAND POCKY CHOCOLATE 38GM", "CHOCOLATE", "0000052868789"),
            ("GLICO BRAND POCKY MATCHA 38GM", "MATCHA", "0000052868790"),
        ],
        "OREO": [
            ("OREO ORIGINAL SANDWICH COOKIES 137GM", "ORIGINAL", "0000044000028"),
            ("OREO DOUBLE STUF COOKIES 157GM", "DOUBLE STUF", "0000044000029"),
            ("OREO GOLDEN COOKIES 154GM", "GOLDEN", "0000044000030"),
        ],
        "LAY'S": [
            ("LAY'S CLASSIC POTATO CHIPS 150GM", "CLASSIC", "0000028400010"),
            ("LAY'S SOUR CREAM & ONION 150GM", "SOUR CREAM", "0000028400011"),
            ("LAY'S BBQ CHIPS 150GM", "BBQ", "0000028400012"),
        ],
        "COCA-COLA": [
            ("COCA-COLA CLASSIC 500ML PET", "CLASSIC", "0000049000028"),
            ("COCA-COLA ZERO SUGAR 500ML", "ZERO", "0000049000029"),
            ("COCA-COLA CHERRY 500ML", "CHERRY", "0000049000030"),
        ],
        "PEPSI": [
            ("PEPSI COLA 500ML BOTTLE", "REGULAR", "0000012000028"),
            ("PEPSI MAX 500ML", "MAX", "0000012000029"),
            ("PEPSI LIME 500ML", "LIME", "0000012000030"),
        ],
    }
    
    manufacturers = {
        "POCKY": "EZAKI GLICO",
        "OREO": "MONDELEZ INTERNATIONAL",
        "LAY'S": "FRITO-LAY",
        "COCA-COLA": "THE COCA-COLA COMPANY",
        "PEPSI": "PEPSICO",
    }
    
    sizes = {
        "POCKY": "38GM",
        "OREO": "137GM",
        "LAY'S": "150GM",
        "COCA-COLA": "500ML",
        "PEPSI": "500ML",
    }
    
    # Generate data rows
    data_rows = []
    
    for brand, products in brands_products.items():
        for item, variant, upc in products:
            # Create multiple rows for same product (to test merging)
            num_duplicates = random.randint(1, 5)
            
            for _ in range(num_duplicates):
                row = {
                    "Markets": "Pen Malaysia",
                    "Product Segment": "TOTAL BISCUITS" if brand in ["POCKY", "OREO"] else "BEVERAGES",
                    "MANUFACTURER": manufacturers[brand],
                    "MPACK": "X1",
                    "NRMSIZE": sizes[brand],
                    "BRAND": brand,
                    "ITEM": item,
                    "UPC": upc,
                    "VARIANT": variant,
                    "Facts": "Sales Value",
                }
                
                # Add monthly columns (w/e dates)
                months = [
                    "Dec 23 - w/e 31/12/23",
                    "Jan 24 - w/e 31/01/24",
                    "Feb 24 - w/e 29/02/24",
                    "Mar 24 - w/e 31/03/24",
                    "Apr 24 - w/e 30/04/24",
                    "May 24 - w/e 31/05/24",
                    "Jun 24 - w/e 30/06/24",
                    "Jul 24 - w/e 31/07/24",
                    "Aug 24 - w/e 31/08/24",
                    "Sep 24 - w/e 30/09/24",
                    "Oct 24 - w/e 31/10/24",
                    "Nov 24 - w/e 30/11/24",
                ]
                
                for month in months:
                    # Generate random sales values (some zeros, some with values)
                    if random.random() > 0.3:  # 70% chance of having sales
                        row[month] = round(random.uniform(100, 500), 2)
                    else:
                        row[month] = 0.0
                
                # Add MAT (Moving Annual Total)
                row["MAT Nov'24"] = round(sum([row[m] for m in months]), 2)
                
                data_rows.append(row)
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data_rows)
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Malaysia_Sales", index=False)
    
    print(f"✅ Generated {filename} with {len(data_rows)} rows")
    print(f"📊 Brands: {', '.join(brands_products.keys())}")
    print(f"🔢 Total products: {sum(len(p) for p in brands_products.values())}")
    print(f"📦 Rows per product will vary (1-5) to test merging")

if __name__ == "__main__":
    generate_realistic_mock_data()
