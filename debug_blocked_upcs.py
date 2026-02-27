from mapping_analysis import validate_match, normalize_text

# Example 1: Orange Sandwich
desc_7e_1 = "Julie's Cream Sandwich Orange 100g"
master_doc_1 = {"ITEM": "JULIE'S CREAM S/WICH ORANGE 100 GM", "variant": "NONE"}
brand_7e = "Julie's"
print(f"Goal: {desc_7e_1} -> {master_doc_1['ITEM']}")
res1 = validate_match(desc_7e_1, master_doc_1, "ORANGE", None, brand_7e, is_upc_match=True)
print(f"Result: {res1}\n")

# Example 2: Choco More
desc_7e_2 = "Julie's Choco More Sandwich 160g"
master_doc_2 = {"ITEM": "JULIE'S CHCO MORE SANDWICH 132G", "variant": "NONE"}
print(f"Goal: {desc_7e_2} -> {master_doc_2['ITEM']}")
res2 = validate_match(desc_7e_2, master_doc_2, "CHOCOLATE", "CHOCO MORE", brand_7e, is_upc_match=True)
print(f"Result: {res2}\n")

# Example 3: Peanut Sandwich
desc_7e_3 = "Julie's My Peanut Butter 90g"
master_doc_3 = {"ITEM": "JULIE'S MY PEANUT SANDWICH 90 GM", "variant": "NONE"}
print(f"Goal: {desc_7e_3} -> {master_doc_3['ITEM']}")
# Here 7E has 'PEANUT BUTTER' in name but master has 'PEANUT SANDWICH'
# flavour_7e might be 'NONE' according to user's dump
res3 = validate_match(desc_7e_3, master_doc_3, "NONE", None, brand_7e, is_upc_match=True)
print(f"Result: {res3}\n")

# Example 4: Dark Choco
desc_7e_4 = "Julie'S Dark Choco Sandwich 58g"
master_doc_4 = {"ITEM": "JULIES DARK CHOCO VANILLA 58GM", "variant": "NONE"}
print(f"Goal: {desc_7e_4} -> {master_doc_4['ITEM']}")
res4 = validate_match(desc_7e_4, master_doc_4, "CHOCOLATE", None, brand_7e, is_upc_match=True)
print(f"Result: {res4}\n")
