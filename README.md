# Advanced Twitter Data Analysis: Extraction, Content Filtering, and Interaction Network Modeling (Retweets, Mentions, and Coretweets)

This Python project processes Twitter data, specifically focusing on retweets, mentions, and coretweets. It includes a Python script that performs extensive data mining and network analysis, utilizing JSON and BZ2 files. The script filters and processes tweet metadata related to hashtags, retweets, and mentions, and visualizes user interactions within a Twitter dataset. Additionally, it constructs graph representations of retweet, mention, and coretweet networks, exporting them in GEXF format for advanced network analysis.

## Requirements

This project requires the following Python libraries:
- `networkx`: For creating and manipulating graphs.
- `mpi4py`: For parallel processing using MPI.
- `json`: For handling JSON data.
- `bz2`: For working with `.bz2` compressed files.
- `shutil`: For file operations (e.g., copying files).
- `datetime`: For date manipulation.
- `time`: For measuring execution time.

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

# Parallelism in Code with MPI

The code uses **MPI** (Message Passing Interface) to implement **parallel processing**, which allows work to be divided between multiple processes to improve efficiency and speed up processing of large volumes of data. Below we explain how parallelism was implemented, the benefits it brought, and what it was used for.

## How was parallelism used?

Parallelism in this code was implemented using the `mpi4py` package to distribute work across multiple processes efficiently.

1. **MPI Initialization:**
The code uses the `MPI.COMM_WORLD` function to create a global communicator that allows interaction between different processes:
```python
comm = MPI.COMM_WORLD
rank = comm.Get_rank() # Unique ID of the current process
size = comm.Get_size() # Total number of processes
```

2. **Division of work:** The JSON files to be processed are divided into several "chunks" according to the total number of processes (size). This allows the workload to be distributed evenly among all available processes:
```python
chunks = [files_to_process[i::size] for i in range(size)]
```

3. **Distribution of files to be processed:** The "chunks" are distributed among the processes using comm.scatter, which allows each process to receive a set of files to process:
```python
files_to_process = comm.scatter(chunks, root=0)
```

4. **Parallel processing:** Each process processes the assigned files independently. Processing consists of extracting and filtering tweets according to certain criteria (such as hashtags and dates), and storing the results locally in each process:
```python
for file in files_to_process:
tweets_data. extend(merged_output(file, hashtags_to_find, start_date, end_date))
```

5. **Gathering results:** Once all processes have completed their work, the results (processed tweet data) are collected in the root process (rank 0) using comm.gather:
```python
all_tweets_data = comm.gather(tweets_data, root=0)
```

6. **Consolidation and saving:** Finally, the root process combines all the results from the different processes and saves the consolidated file with the processed data:
```python
merged_tweets = []
for data in all_tweets_data:
merged_tweets. extend(data)
with open(output_file, 'w', encoding='utf-8') as output_file:
json. dump(merged_tweets, output_file, ensure_ascii=False, indent=2)
```

## What was parallelism used for?
Parallelism in this code was used to process large volumes of data (in this case, JSON files with tweet data) more efficiently. Using MPI allowed:

- Splitting data files into smaller parts and distributing them between processes.
- Filtering and processing tweets independently and simultaneously.
- Reducing overall execution time, especially when you have many large files.
-
Parallelism allows the system to handle more data in less time, which is crucial when working with large databases or when processing speed is an important factor.


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
