# Docchi.pl Addon for Kodi

![Version](https://img.shields.io/badge/version-0.2.4.2-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-Active-brightgreen.svg)

<div align="center">
  <img src="https://docchi.pl/static/img/logo.svg" alt="Docchi.pl Logo" width="300">
</div>

An addon for Kodi that allows users to watch anime with Polish subtitles from the [**Docchi.pl**](http://docchi.pl) site. This project is a port of mine **[original Stremio addon](https://github.com/skoruppa/docchi-stremio-addon)**, bringing its core logic to the Kodi platform.

---

## Key Features

- **Access to Docchi.pl Catalogs**: Browse anime from the current season, view trending series, and see the latest released episodes.
- **Rich Metadata from Kitsu**: All lists are enhanced with detailed information such as descriptions, ratings, premiere dates, genres, and posters thanks to integration with the Kitsu API.
- **Detailed Episode Information**: The episode list includes individual titles, synopses, and thumbnails when available from Kitsu.
- **Intelligent Caching**: The addon uses a local SQLite database to cache ID mappings and metadata, which drastically speeds up loading times on subsequent visits.

## Installation

There are two installation methods: the recommended one (using the repository for automatic updates) and a manual one (for a single installation).

### Recommended Installation (from the Docchipl Repository)

This method is recommended as it provides **automatic updates** for the addon whenever a new version is released. It's a two-step process: first, you install the repository, and then you install the addon from it.

#### Step 1: Install the Docchipl Repository

1.  Add `skoruppa.github.io/plugin.video.docchipl` as a file manager's source or download the repository ZIP file by clicking the link below:
    *   [**repository.docchipl.zip**](https://skoruppa.github.io/plugin.video.docchipl/repository.docchipl.zip)
2.  Open Kodi and navigate to: **Add-ons -> Add-on browser (the box icon)**.
3.  Select **Install from zip file**.
4.  Select the added source or locate the downloaded `repository.docchipl.zip` file and confirm the installation.
5.  Wait for the notification confirming the repository has been installed successfully.

#### Step 2: Install the Docchi.pl Addon

1.  In the same Add-on browser, select **Install from repository**.
2.  Select **Docchipl Repo** from the list.
3.  Go to the **Video add-ons** category.
4.  Select **Docchi.pl** from the list and click **Install**.
5.  After a moment, the addon will be installed and available in **Add-ons -> Video add-ons**.

### Alternative Method (Manual Installation from ZIP file)

You can install the addon manually, but please note that this method **does not provide automatic updates**.

1.  Navigate to the [**Releases**](https://github.com/skoruppa/plugin.video.docchipl/releases) section of this GitHub page.
2.  Download the latest version of the addon as a `.zip` file (e.g., `plugin.video.docchipl-0.2.4.2.zip`).
3.  Open Kodi and navigate to: **Add-ons -> Add-on browser (the box icon)**.
4.  Select **Install from zip file**.
5.  Locate the `.zip` file you just downloaded and confirm the installation.
6.  After a moment, the addon will be installed and available in **Add-ons -> Video add-ons**.

## How It Works (Architecture)

The addon uses a hybrid approach, combining data from two sources to provide the best possible user experience:

- **Docchi.pl API**: Serves as the primary source of truth for which anime and episodes are available, and for fetching the list of stream links.
- **Kitsu.io API**: Used to fetch all rich metadata—both for entire series (descriptions, genres, ratings, artwork) and for individual episodes (titles, synopses, thumbnails).
- **Local Database (SQLite)**: The addon intelligently saves fetched metadata to a local database. This ensures that when you reopen a list, the data loads almost instantly without needing to query the APIs again.

## Supported Players
As the stream data needs to be extracted from web players, not all available players at Docchi.pl are supported
- **Uqload**
- **CDA**
- **OK.ru**
- **VK.com**
- **Sibnet.ru**
- **Lycoris.cafe**
- **Dailymotion**
- **Google Drive**
- **Rumble.com**
- **Bigwarp.io**
- **Lulustream**
- **Streamhls.to**
- **Streamtape.com**
- **Vidtube.one**
- **RPMHub**
- **UPNS**
- **MP4Upload**
- **Filemoon**
- **EarnVid**
- **StreamUP**
- **Vidguard**

## Acknowledgements

- **Original Stremio Addon**: The entire player resolver logic and general architecture was ported from the **[author's original project for Stremio](https://github.com/skoruppa/docchi-stremio-addon)**.
- **The Kodi Community**: For creating open and flexible software.

## Reporting Bugs

If you encounter any issues, please report them in the [**Issues**](https://github.com/skoruppa/plugin.video.docchipl/issues) section of this repository. Include a snippet from your Kodi log to help diagnose the problem.

## Support 🤝

If you want to thank me for the addon, you can [**buy me a coffe**](https://buymeacoffee.com/skoruppa) 
