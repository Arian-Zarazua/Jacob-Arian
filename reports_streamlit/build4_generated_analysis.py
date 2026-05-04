import argparse
import pandas as pd

def load_data(data_path: str) -> pd.DataFrame:
    import pathlib
    p = pathlib.Path(data_path)
    if p.is_file():
        return pd.read_csv(p)
    files = sorted(p.glob('*.csv'))
    if not files:
        raise FileNotFoundError('No CSVs found in ' + str(p))
    frames = []
    for f in files:
        part = pd.read_csv(f)
        part['_source_file'] = f.stem
        frames.append(part)
    return pd.concat(frames, ignore_index=True, sort=False)

def main():
    parser = argparse.ArgumentParser(description='Process NFL data.')
    parser.add_argument('--data', required=True, help='Path to CSV file or directory containing CSV files.')
    parser.add_argument('--report_dir', required=True, help='Directory to save the report.')

    args = parser.parse_args()

    # Load the data
    df = load_data(args.data)

    # Validate required columns
    required_columns = ['season', 'event_date', 'alias', 'rush_att', 'pass_cmp', 'pass_att']
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Required column '{col}' is missing.")
            exit(1)

    # Handle missing values with listwise deletion
    df = df.dropna()

    # Remove the '_source_file' column
    if '_source_file' in df.columns:
        df = df.drop(columns=['_source_file'])

    # Save the cleaned DataFrame to a new CSV file in the report directory
    output_file = f"{args.report_dir}/cleaned_data.csv"
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    main()