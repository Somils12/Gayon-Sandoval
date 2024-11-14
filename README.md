# Advanced Twitter Data Analysis: Extraction, Content Filtering, and Interaction Network Modeling (Retweets, Mentions, and Coretweets)

This project contains a Python script that performs extensive data mining and network analysis on Twitter data, leveraging JSON and BZ2 files. It filters, processes, and visualizes tweet metadata related to hashtags, retweets, and mentions, allowing for in-depth insights into user interactions within a Twitter dataset. The script also constructs graph representations of retweet, mention, and coretweet networks, exporting them in GEXF format for advanced network analysis.

## Project Structure
- **Input Data**: The primary input files are compressed JSON files (`.json.bz2`) containing tweet metadata.
- **Output Files**:
  - `merged_output.json`: Merged and filtered tweets based on hashtag presence and date range.
  - `rt.json`: JSON file aggregating retweets data.
  - `mencion.json`: JSON file aggregating mention data.
  - `corrtw.json`: JSON file aggregating coretweet data (mutual retweets between user pairs).
  - Graph files in GEXF format for visualization and further analysis in external tools like Gephi:
    - `rt.gexf`: Graph of retweet interactions.
    - `mencion.gexf`: Graph of mentions.
    - `corrtw.gexf`: Coretweet graph.

## Features and Functionalities
- **File Retrieval and Date Filtering**: The script searches a specified directory for `.json.bz2` files. It filters these files based on user-defined start and end dates, extracting tweet data within the specified timeframe.
- **Hashtag Filtering**: User-defined hashtags can be specified via a text file. The script retains only tweets containing at least one of the listed hashtags.
- **Data Extraction**: For each filtered tweet, relevant information (e.g., tweet ID, user details, text, hashtags, URLs, and mentions) is extracted and saved in `merged_output.json`.
- **Network Analysis**:
  - **Retweet Network**: The script constructs a retweet network, tracking which users retweeted specific tweets and aggregating total retweet counts per user.
  - **Mention Network**: Mentions are extracted to create a directed graph, showing which users mentioned others in their tweets.
  - **Coretweet Network**: Analyzes mutual retweet patterns, identifying pairs of users who have been retweeted by common users. The resulting graph is weighted by the number of mutual retweets.
- **Graph Export**: Exports retweet, mention, and coretweet networks in GEXF format, enabling visualization in network analysis tools.
- **Output Cleanup**: Intermediate files and directories are deleted post-processing for efficient storage management.

## Usage
The script can be run from the command line with various parameters:

```bash
python script_name.py -d <directory> -h <hashtag_file> -fi <start_date> -ff <end_date> [options]
```

# Script Documentation

## Parameters
- `-d <directory>`: Specifies the root directory containing the `.json.bz2` files.
- `-h <hashtag_file>`: Specifies the path to a text file listing hashtags for filtering.
- `-fi <start_date>` and `-ff <end_date>`: Define the date range (in `dd-mm-yyyy` format) for filtering tweet data.

### Additional Flags
- `--grt`: Generate retweet graph.
- `--jrt`: Generate retweet JSON.
- `--gm`: Generate mention graph.
- `--jm`: Generate mention JSON.
- `--gcrt`: Generate coretweet graph.
- `--jcrt`: Generate coretweet JSON.

## Example

```bash
python script_name.py -d "./data" -h "hashtags.txt" -fi "01-01-2023" -ff "31-12-2023" --grt --gm --gcrt
```


This README.md provides a clear, structured, and detailed guide for understanding the functionalities, usage, and requirements of the script, aligning it with high standards for data analysis and network research documentation.
