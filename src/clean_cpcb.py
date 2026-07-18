def clean_cpcb(df):

    df = df.copy()

    df = df.dropna()

    numeric_cols = [
        "PM2_5",
        "PM10",
        "NO2",
        "O3"
    ]

    for col in numeric_cols:

        df.loc[:, col] = (
            df[col]
            .astype(float)
        )

    return df