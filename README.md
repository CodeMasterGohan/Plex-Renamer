# Plex-Optimized Media Renamer

A desktop application that scans movie and TV show files and renames them according to Plex naming conventions using metadata from TMDB and TVDB APIs.

## Features

- **Multi-Source Metadata**: Integrates with TMDB and TVDB APIs for comprehensive movie and TV show information
- **Plex Naming Compliance**: Automatically renames files according to Plex naming conventions
- **Network Drive Support**: Designed to work with mapped network drives (e.g., Z:\Plex)
- **Flexible Organization**: Separate handling for movies and TV shows with configurable folder structures
- **Dry Run Mode**: Preview changes before execution
- **User-Friendly GUI**: Easy-to-use desktop interface
- **Comprehensive Logging**: Track all operations and errors
- **Configurable Settings**: Customizable paths, API keys, and preferences

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Plex-Renamer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Configuration

Before using the application, you'll need to:

1. **Get API Keys**:
   - TMDB API key from [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
   - TVDB API key from [https://thetvdb.com/dashboard/account/apikey](https://thetvdb.com/dashboard/account/apikey)

2. **Set Media Paths**:
   - Configure your base media directory (e.g., Z:\Plex)
   - Set subfolder paths for movies and TV shows

## Naming Conventions

### Movies
- **Format**: `Movie Title (Release Year).ext`
- **Optional Folder Structure**: `movies/Movie Title (Release Year)/Movie Title (Release Year).ext`

### TV Shows
- **Format**: `tv_shows/Show Name (Release Year)/Season XX/Show Name - sXXeYY - Episode Title.ext`
- **Optional ID**: `Show Name (Release Year) {tvdb-12345}` or `{tmdb-######}`

## Usage

1. Launch the application
2. Configure your API keys and media paths in Settings
3. Select the media type to scan (Movies or TV Shows)
4. Review the proposed changes in Dry Run mode
5. Apply changes when satisfied

## License

This project is open source and available under the MIT License. 