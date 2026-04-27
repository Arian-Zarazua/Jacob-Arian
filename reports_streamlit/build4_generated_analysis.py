import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    parser = argparse.ArgumentParser(description='Analyze NFL data.')
    parser.add_argument('--data', required=True, help='Path to CSV file or directory of CSV files')
    parser.add_argument('--report_dir', required=True, help='Directory to save reports and visualizations')
    args = parser.parse_args()

    # Load data
    df = load_data(args.data)

    # Validate required columns
    required_columns = ['penalties', 'turnovers', 'time_of_possession', 'total_yds']
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Required column '{col}' is missing from the dataset.")
            exit(1)

    # Handle missing values with listwise deletion
    df = df.dropna(subset=required_columns)

    # Statistical summaries
    summary = df[required_columns].describe()
    summary_path = f"{args.report_dir}/summary_statistics.csv"
    summary.to_csv(summary_path)

    # Visualizations
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=df, x='penalties', y='time_of_possession', hue='turnovers', palette='viridis', alpha=0.7)
    plt.title('Penalties vs Time of Possession colored by Turnovers')
    plt.xlabel('Number of Penalties')
    plt.ylabel('Time of Possession (in seconds)')
    plt.savefig(f"{args.report_dir}/penalties_vs_time_of_possession.png")
    plt.close()

    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x='turnovers', y='total_yds')
    plt.title('Total Yards by Turnovers')
    plt.xlabel('Number of Turnovers')
    plt.ylabel('Total Yards')
    plt.savefig(f"{args.report_dir}/total_yards_by_turnovers.png")
    plt.close()

if __name__ == "__main__":
    main()