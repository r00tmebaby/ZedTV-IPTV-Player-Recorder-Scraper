# Changelog

All notable changes to ZedTV IPTV Player will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2025-12-13

### Added
- **Fullscreen Timer Display**
  - Dynamic timer in fullscreen overlay showing current time / total time
  - Updates every 500ms just like the small window
  - Shows playback speed when not at 1.0x (e.g., "12:34 / 1:23:45 (1.5x)")
  - Automatically formats as HH:MM:SS for long videos
  - Timer starts/stops automatically with overlay visibility
  
- **Comprehensive Debug Logging**
  - Added detailed logging throughout fullscreen timer updates
  - Captures data types, values, and calculation steps
  - Full exception stack traces for easier troubleshooting
  - Helps identify issues quickly with step-by-step execution logs

### Changed
- **Global Search Enhancements**
  - Removed Play button - now uses intuitive double-click or Enter key to play
  - When playing from search, category is automatically selected in left panel
  - Channel list refreshes to show the selected category
  - Playing video is highlighted in the channel list
  - Visual feedback shows exactly what's playing and where it belongs

### Fixed
- **ESC Key Reliability**
  - Fixed ESC key not working after multiple seeks in fullscreen
  - Properly manages exit flag lifecycle to prevent stuck states
  - Timer cleanup on exit prevents orphaned update jobs
  - ESC now works consistently every time, even after extensive seeking

## [1.6.0] - 2025-12-12

### Added
- **Fullscreen Overlay Controls**
  - New keyboard-friendly control bar with icons in fullscreen
  - ESC reliably exits fullscreen even when buttons have focus
  - Added keyboard shortcuts for subtitles (S), audio (A), speed (D), seeking (arrows), pause/play (Space)
  - Overlay toggles with 'C' key and fades out when not needed
  - Beautiful icon buttons at bottom of screen
  - All controls accessible via keyboard or mouse

- **Keyboard Shortcuts Configuration**
  - Configurable keyboard bindings in UI Settings
  - Users can customize all fullscreen shortcuts
  - Default bindings: ESC (exit), C (toggle controls), S (subtitles), A (audio), D (speed)

### Changed
- **Improved Window Management**
  - Fullscreen minimize/maximize flow fixed so the entire app minimizes together
  - Control buttons stay disabled until playback actually starts, avoiding stuck states
  - Better window synchronization between main, category, and channel windows

### Fixed
- **Playback Enhancements**
  - Subtitles menu available directly in fullscreen overlay
  - Video timers reset correctly when starting a new VOD
  - Timers update live with playback speed display
  - Settings persistence fixes (subtitle/audio/speed remembered when toggling fullscreen)
  - Fixed subtitle track selection being lost when entering/exiting fullscreen

- **Global Search Improvements**
  - Ctrl+F window shows channel metadata clearly
  - Double-click to play functionality improved
  - Searches entire catalog regardless of selected category

## [1.5.0] - 2025-12-10

### Added
- **Global Search (Ctrl+F)**
  - Search across ALL channels and videos instantly (not limited to categories)
  - Case-insensitive, starts-with matching for fast filtering
  - Live results as you type
  - Double-click or press Enter to play directly from search results
  - Shows channel title, category, rating, and year in organized table
  - Access via View menu or Ctrl+F keyboard shortcut

- **Major UI Overhaul**
  - Changed the layout from static to dynamic windows (WinAmp-style)
  - Clean, modern tabbed interface for all settings windows
  - Filter categories and channels with instant search boxes
  - New Logs menu with options to view current log and open logs folder
  - Added background image when idle (no playback)
  - Added loading spinner when loading M3U or switching accounts
  - Added helpful tooltips on buttons and inputs
  - Added help menu with links to README, issues, license
  - 70+ color themes with live preview
  - Customizable fonts and sizes for all UI elements
  - One-click font size presets (Small/Medium/Large/XL)

- **UI Settings Window** (tabbed)
  - **Theme tab**: 70+ color themes with live preview
  - **Fonts tab**: Customize font family and sizes for all UI elements
  - **Presets tab**: One-click font size presets

- **VLC Settings Window** (tabbed)
  - **Network tab**: Buffer settings for smooth streaming
  - **Video & Audio tab**: Hardware acceleration, output options, volume control
  - **Advanced tab**: Performance tweaks and maintenance options

- **Logging Settings Window**
  - Configure log levels, file rotation, retention policies
  - Mirror logs to console for debugging
  - Clean, organized interface with helpful descriptions

### Fixed
- IP Info window now works properly with Refresh button
- Better error handling with user-friendly messages
- All settings windows use consistent, polished layouts
- Improved spacing, padding, and button alignment throughout
- Fixed various minor bugs and UI glitches

### Changed
- Settings organized into logical groups (no more endless scrolling)
- Larger fonts and better readability across the board
- Consistent design language and polished look & feel
- Improved overall user experience and navigation

## [1.4.0] - 2025-12-05

### Added
- **Xtream Codes Integration**
  - Full account management system
  - Add/manage multiple accounts with snapshots
  - Auto-generate enriched M3U playlists
  - View account status, expiry, connection limits
  - Refresh snapshots to update server info

- **VLC Player Settings**
  - Configurable network buffering
  - Hardware acceleration options
  - Audio/video output settings
  - Advanced performance tweaks

- **Session Restore**
  - Automatically remembers last used account or M3U file
  - Fast startup with previous session state

- **Recording Feature**
  - Record to MP4 while watching
  - Live preview during recording
  - Configurable output directory

### Changed
- Fast startup time (1-2 seconds)
- Improved error handling and user feedback
- Better logging system with rotation

### Fixed
- Various stability improvements
- Memory leak fixes
- Playback control reliability

## [1.3.0] - 2025-11-28

### Added
- Initial public release
- M3U playlist parser
- Category and channel browsing
- VLC-based playback
- Basic UI with PySimpleGUI
- Custom playlist creator

---

## Version History

- **[1.6.1]** - 2025-12-13: Fullscreen timer, ESC key fix, visual selection improvements
- **[1.6.0]** - 2025-12-12: Fullscreen overlay controls, keyboard shortcuts
- **[1.5.0]** - 2025-12-10: Global search, major UI overhaul, tabbed settings
- **[1.4.0]** - 2025-12-05: Xtream Codes, VLC settings, session restore
- **[1.3.0]** - 2025-11-28: Initial release

---

## Links

- [GitHub Repository](https://github.com/r00tmebaby/ZedTV-IPTV-Player-Recorder-Scraper)
- [Issue Tracker](https://github.com/r00tmebaby/ZedTV-IPTV-Player-Recorder-Scraper/issues)
- [Latest Release](https://github.com/r00tmebaby/ZedTV-IPTV-Player-Recorder-Scraper/releases/latest)

