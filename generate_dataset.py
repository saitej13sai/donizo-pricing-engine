import csv, random, datetime, pathlib
pathlib.Path("data").mkdir(parents=True, exist_ok=True)

regions = ["Île-de-France", "PACA", "Auvergne-Rhône-Alpes", "Occitanie", "Belgium"]
units = ["€/m²", "€/kg", "€/liter", "€/unit"]
vendors = ["Castorama", "Leroy Merlin", "PointP", "Brico", "Brico Dépôt", "DonizoSim"]
names = [
 ("HydroFix Waterproof Adhesive", "High-bond waterproof tile adhesive for interior walls; wet areas like shower; white"),
 ("Matte White Ceramic Tile 60x60", "60x60cm waterproof ceramic tile, matte finish, wall, indoor, bathroom"),
 ("Outdoor Cement Mix", "Weather-resistant cement mix for outdoor tiling, durable; suitable for patios"),
 ("Primer Seal Coat", "Primer for porous surfaces; improves adhesion; interior"),
 ("Grout Anti-Mold White", "Tile grout with anti-mold additive; white; bathroom and kitchen use")
]
srcs = [
 "https://www.leroymerlin.fr/produit/hydrofix-adhesive",
 "https://www.castorama.fr/produit/matte-white-ceramic-tile-60x60",
 "https://www.pointp.fr/produit/outdoor-cement-mix",
 "https://www.brico.be/produit/primer-seal-coat",
 "https://www.bricodepot.fr/produit/grout-anti-mold-white"
]
def price_for(unit):
    if unit=="€/kg": return round(random.uniform(1.5, 3.5), 2)
    if unit=="€/liter": return round(random.uniform(5.0, 15.0), 2)
    if unit=="€/m²": return round(random.uniform(12.0, 45.0), 2)
    return round(random.uniform(2.0, 25.0), 2)

random.seed(17)
now = datetime.datetime(2025,8,3,14,30,0, tzinfo=datetime.timezone.utc)
rows = []
for i in range(1200):
    idx = random.randint(0, len(names)-1)
    name, desc = names[idx]
    unit = random.choice(units)
    rows.append({
        "material_name": name if idx!=0 else ("HydroFix Waterproof Adhesive" if random.random()<0.7 else "HydroFix Tile Glue White"),
        "description": desc,
        "unit_price": price_for(unit),
        "unit": unit,
        "region": random.choice(regions),
        "vendor": random.choice(vendors),
        "vat_rate": random.choice([10, 20, ""]),
        "quality_score": random.randint(1,5),
        "updated_at": now.isoformat().replace("+00:00","Z"),
        "source": srcs[idx]
    })

with open("data/materials.csv","w",newline="",encoding="utf-8") as f:
    wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wtr.writeheader(); wtr.writerows(rows)
print("Wrote data/materials.csv with", len(rows), "rows")
