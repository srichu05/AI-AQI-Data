def add_coordinates(df):

    district_coords = {

        "bagalkot": (16.18, 75.69),
        "belagaum": (15.85, 74.50),
        "bengaluru": (12.97, 77.59),
        "bidar": (17.91, 77.52),
        "chamrajnagar": (11.92, 76.95),
        "chikballapur": (13.43, 77.73),
        "chikkamanagaluru": (13.31, 75.77),
        "davangere": (14.46, 75.92),
        "dharward": (15.46, 75.00),
        "gadag": (15.43, 75.63),
        "hassan": (13.01, 76.10),
        "haveri": (14.80, 75.40),
        "hubballi": (15.36, 75.12),
        "kalaburagi": (17.33, 76.83),
        "karwar": (14.80, 74.13),
        "kolar": (13.13, 78.13),
        "koppal": (15.35, 76.15),
        "madikeri": (12.42, 75.73),
        "mangalore": (12.91, 74.85),
        "mysuru": (12.30, 76.65),
        "raichur": (16.20, 77.37),
        "ramanagara": (12.72, 77.28),
        "shimoga": (13.93, 75.56),
        "tumakaru": (13.34, 77.10),
        "udupi": (13.34, 74.75),
        "vijayapura": (16.83, 75.71),
        "yadgir": (16.77, 77.14)
    }

    df["lat"] = df["district"].map(
        lambda x: district_coords[x][0]
    )

    df["lon"] = df["district"].map(
        lambda x: district_coords[x][1]
    )

    return df