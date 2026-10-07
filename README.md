# Algorithmic Book Analytics Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/DSA-Mid--Term%20Project-6A1B9A?style=for-the-badge" alt="DSA Project">
</p>

<p align="center">
  A desktop-based book data scraping, searching, sorting, and analytics system
  developed as a Data Structures & Algorithms project.
</p>

---

## Overview

The **Algorithmic Book Analytics Engine** is a Python-based desktop application designed to demonstrate the practical application of **Data Structures and Algorithms** on a large book dataset.

The system combines:

* Multi-threaded web scraping
* Real-time scraping progress tracking
* Advanced searching and filtering
* Multiple custom sorting algorithms
* Algorithm performance benchmarking
* Multi-level sorting
* Dataset management
* Interactive PyQt6 graphical interface

The application is designed to handle a dataset of **15,000+ book records** while keeping the graphical interface responsive during long-running scraping and processing operations.

---

## Key Features

### Web Scraping

* Scrapes book information from a configurable target URL.
* Supports datasets containing **15,000+ book entities**.
* Stores scraped data in CSV format.
* Displays real-time scraping progress.
* Supports task control through:

  * Start
  * Pause
  * Resume
  * Stop
* Uses `QThread` to prevent the GUI from freezing during scraping.

### Book Attributes

Each book record contains at least eight attributes:

| Attribute | Description       |
| --------- | ----------------- |
| ID        | Unique identifier |
| Title     | Book title        |
| Author    | Book author       |
| Price     | Book price        |
| Rating    | Book rating       |
| Year      | Publication year  |
| Pages     | Number of pages   |
| Category  | Book category     |

---

## Searching & Filtering

The application provides flexible search functionality for exploring the scraped dataset.

### String Matching

Supported search operations include:

* Contains
* Starts With
* Ends With
* Exact Match

### Boolean Filtering

Multiple filtering rules can be combined using:

* `AND`
* `OR`
* `NOT`

This allows users to construct compound queries across different book attributes.

### Example

A user could search for:

```text
Category = Fiction
AND
Rating >= 4
AND
Price < 2000
```

---

## Sorting Algorithms

The project implements and benchmarks six sorting algorithms:

| Algorithm      |      Average Complexity |   Worst-Case Complexity | Stable |
| -------------- | ----------------------: | ----------------------: | :----: |
| Bubble Sort    |                   O(n²) |                   O(n²) |   Yes  |
| Selection Sort |                   O(n²) |                   O(n²) |   No   |
| Insertion Sort |                   O(n²) |                   O(n²) |   Yes  |
| Merge Sort     |              O(n log n) |              O(n log n) |   Yes  |
| Shell Sort     | Depends on gap sequence | Depends on gap sequence |   No   |
| TimSort        |              O(n log n) |              O(n log n) |   Yes  |

The sorting module is implemented separately so that the algorithms can be tested and benchmarked independently.

---

## Algorithm Benchmarking

The application includes a dedicated benchmarking system for comparing sorting algorithms.

The benchmark engine records:

* Execution time
* Number of comparisons
* Number of swaps
* Algorithm complexity
* Stability information

Execution time is measured using Python's high-resolution:

```python
time.perf_counter()
```

### Benchmark Comparison

The GUI provides a side-by-side comparison of the available algorithms, allowing users to observe how different algorithms perform on the same dataset.

The sorting scope can also be changed between:

* **Full Dataset**
* **Filtered Dataset**

This makes it possible to compare algorithm performance under different data conditions.

---

## Multi-Level Sorting

The application supports compound sorting using multiple attributes.

For example:

```text
Primary: Rating → Descending
Secondary: Price → Ascending
```

This allows books with the same rating to be further ordered according to their price.

The implementation uses tuple-based keys for multi-column sorting.

---

## Multi-Threaded Scraping

A major component of the project is the multi-threaded scraping engine.

The scraper uses:

* `QThread`
* `QMutex`
* `QWaitCondition`

These synchronization mechanisms allow the scraping process to be controlled without blocking the main GUI thread.

### Task States

```text
START
  ↓
SCRAPING
  ↓
PAUSE ─────→ RESUME
  ↓
STOP
```

The system continuously communicates progress from the worker thread to the GUI.

---

## Progress Tracking

The GUI provides real-time feedback during scraping.

The progress interface displays:

* Current progress
* Number of entities scraped
* Total target entities
* Current task status

Example:

```text
Scraping Books...

████████████████░░░░░░░░  68%

10,200 / 15,000 books
```

---

## Dynamic Target URL

The application provides a URL input field that allows users to specify the scraping target dynamically.

Instead of hard-coding a single website, the application can accept a seed URL through the graphical interface.

```text
Target URL:
[ https://example.com/books                  ]

              [ Start Scraping ]
```

---

# System Architecture

The project follows a modular architecture that separates scraping, algorithms, searching, data models, and GUI components.

```text
                    ┌──────────────────────┐
                    │       main.py        │
                    │   Application Entry  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │     UI     │   │  Scraper   │   │  Analytics │
       │   PyQt6    │   │  QThread   │   │    DSA     │
       └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
             │                │                │
             │                ▼                ├──────────────┐
             │         ┌─────────────┐         │              │
             │         │ CSV Dataset │         ▼              ▼
             │         └─────────────┘  ┌────────────┐ ┌────────────┐
             │                          │  Sorting   │ │  Searching │
             │                          └────────────┘ └────────────┘
             │
             ▼
      ┌────────────────┐
      │ Benchmark GUI  │
      └────────────────┘
```

---

# Project Structure

```text
DSA_Mid_Project/
│
├── data/
│   └── scraped_books.csv
│
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── scraper.py
│   ├── sorting.py
│   └── searching.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   └── benchmark_dialog.py
│
├── main.py
├── requirements.txt
└── README.md
```

### Module Description

| File                  | Purpose                                    |
| --------------------- | ------------------------------------------ |
| `main.py`             | Application entry point                    |
| `models.py`           | Defines the Book data model                |
| `scraper.py`          | Multi-threaded scraping engine             |
| `sorting.py`          | Sorting algorithms and performance metrics |
| `searching.py`        | Searching and Boolean filtering logic      |
| `main_window.py`      | Main PyQt6 application interface           |
| `benchmark_dialog.py` | Algorithm benchmarking interface           |
| `scraped_books.csv`   | Persisted book dataset                     |
| `requirements.txt`    | Python dependencies                        |

---

# Technologies Used

### Programming Language

* Python 3.10+

### GUI Framework

* PyQt6

### Data Processing

* Pandas

### Concurrency

* QThread
* QMutex
* QWaitCondition

### Performance Measurement

* `time.perf_counter()`

### Data Storage

* CSV

### Core Concepts

* Data Structures
* Sorting Algorithms
* Searching Algorithms
* Multi-threading
* Synchronization
* Algorithm Complexity
* Performance Analysis

---

# Installation

## 1. Clone the Repository

```bash
git clone <repository-url>
cd DSA_Mid_Project
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Run the following command from the project root:

```bash
python main.py
```

The PyQt6 application will open with the main dashboard.

---

# Application Workflow

The general workflow is:

```text
Enter Target URL
       ↓
Start Scraping
       ↓
Scrape Book Records
       ↓
Store Dataset
       ↓
Search / Filter Data
       ↓
Select Sorting Algorithm
       ↓
Sort Dataset
       ↓
Benchmark Algorithms
       ↓
Analyze Performance
```

---

# DSA Concepts Demonstrated

This project focuses on the practical implementation of several Data Structures & Algorithms concepts.

### Sorting

* Bubble Sort
* Selection Sort
* Insertion Sort
* Merge Sort
* Shell Sort
* TimSort

### Searching

* String matching
* Attribute-based searching
* Compound filtering
* Boolean query evaluation

### Algorithm Analysis

* Time complexity
* Stability
* Comparison counting
* Swap counting
* Execution-time measurement

### Concurrency

* Thread-based execution
* Mutex synchronization
* Thread pausing and resuming
* Worker-to-GUI communication



# Performance Metrics

For each sorting algorithm, the system can collect:

```text
Algorithm
├── Execution Time
├── Comparisons
├── Swaps
├── Time Complexity
└── Stability
```

These metrics help demonstrate the practical differences between quadratic and logarithmic sorting algorithms.



# Dataset

The application is designed around a large-scale book dataset containing:

```text
15,000+ Book Records
```

Each record contains at least eight attributes:

```text
ID
Title
Author
Price
Rating
Year
Pages
Category
```

The scraped data is persisted in:

```text
data/scraped_books.csv
```



# User Interface

The application uses a dark-themed PyQt6 interface designed around three primary areas:

### Scraping Dashboard

Provides:

* Target URL input
* Start/Pause/Resume/Stop controls
* Progress bar
* Scraping statistics

### Data Explorer

Provides:

* Book dataset table
* Column-based searching
* Boolean filtering
* Multi-level sorting

### Benchmark Dashboard

Provides:

* Algorithm selection
* Performance metrics
* Side-by-side comparison
* Sorting scope selection



# Requirements Compliance

| Requirement                   | Implementation                                          |
| ----------------------------- | ------------------------------------------------------- |
| 15,000+ entities              | Large-scale book dataset                                |
| 8+ attributes                 | ID, Title, Author, Price, Rating, Year, Pages, Category |
| Start scraping                | Implemented                                             |
| Pause scraping                | Implemented                                             |
| Resume scraping               | Implemented                                             |
| Stop scraping                 | Implemented                                             |
| Progress tracking             | Implemented                                             |
| Dynamic URL                   | Implemented                                             |
| GUI                           | PyQt6                                                   |
| Sorting algorithms            | 6 algorithms                                            |
| Benchmarking                  | Execution time, comparisons, swaps                      |
| Complexity information        | Included                                                |
| Stability information         | Included                                                |
| Advanced searching            | Implemented                                             |
| Boolean filtering             | AND / OR / NOT                                          |
| Multi-level sorting           | Implemented                                             |
| Full/filtered dataset sorting | Implemented                                             |



# Future Improvements

Potential future extensions include:

* Database integration using SQLite or PostgreSQL
* Export to Excel and JSON
* Interactive performance charts
* Additional sorting algorithms
* Advanced pagination handling
* Search history
* Dataset deduplication
* Configurable scraping workers
* Automated benchmark reports
* Data visualization dashboard



# Learning Objectives

The project demonstrates how theoretical DSA concepts can be integrated into a practical software application.

The main learning objectives are:

1. Implement sorting algorithms from scratch.
2. Compare algorithmic performance using real data.
3. Understand time complexity and algorithm stability.
4. Implement advanced searching and filtering.
5. Work with large datasets.
6. Understand multi-threaded application design.
7. Implement thread synchronization.
8. Build a responsive desktop GUI.
9. Separate application logic into modular components.
10. Apply DSA concepts to a real-world data processing problem.



# Academic Project

**Project:** Algorithmic Book Analytics Engine
**Course:** Data Structures & Algorithms
**Project Type:** Mid-Term Project
**Technology:** Python + PyQt6
**Dataset:** 15,000+ Book Records




