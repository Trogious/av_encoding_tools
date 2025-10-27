#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <cstdio>
#include <memory>
#include <array>
#include <cmath>
#include <cctype>
#include <cwctype>
#include <algorithm>
#include <iomanip>
#include <codecvt>

#ifdef _WIN32
#include <windows.h>
#endif

bool isVideoFile(const std::wstring& filename) {
    size_t dotPos = filename.find_last_of('.');
    if (dotPos == std::wstring::npos) {
        return false;
    }

    std::wstring ext = filename.substr(dotPos);
    std::transform(ext.begin(), ext.end(), ext.begin(), [](wchar_t c){ return std::towlower(c); });
    return (ext == L".mp4" || ext == L".mkv" || ext == L".webm" || ext == L".avi");
}

std::string execCommand(const std::wstring& cmd) {
    std::array<char, 128> buffer;
    std::string result;

#ifdef _WIN32
    FILE* pipe = _wpopen(cmd.c_str(), L"r");
#else
    FILE* pipe = popen(cmd.c_str(), "r");
#endif

    if (!pipe) {
        std::wcerr << L"Error: Could not open pipe for command: " << cmd << std::endl;
        return "";
    }

    // std::wcerr << L"Executing command: " << cmd << std::endl;
    while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
        result += buffer.data();
    }

#ifdef _WIN32
    _pclose(pipe);
#else
    pclose(pipe);
#endif

    return result;
}

int extractValueFromJson(const std::string& jsonOutput, const std::string& key) {
    size_t pos = jsonOutput.find("\"" + key + "\"");
    if (pos == std::string::npos) {
        return -1.0;
    }

    pos = jsonOutput.find(":", pos);
    if (pos == std::string::npos) {
        return -1.0;
    }

    pos = jsonOutput.find_first_of("\"0123456789", pos + 1);
    if (pos == std::string::npos) {
        return -1.0;
    }

    bool inQuotes = (jsonOutput[pos] == '"');
    if (inQuotes) {
        pos++;
    }

    size_t endPos = pos;
    while (endPos < jsonOutput.size() &&
           (isdigit(jsonOutput[endPos]) || jsonOutput[endPos] == '.')) {
        endPos++;
    }

    std::string valueStr = jsonOutput.substr(pos, endPos - pos);
    try {
        return std::stoi(valueStr);
    } catch (...) {
        return -1;
    }
}

std::wstring findFfprobe() {
    std::vector<std::wstring> hardcodedPaths = {
        L"ffprobe.exe",
        L"C:\\ffmpeg\\bin\\ffprobe.exe",
        L"C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe",
        L"C:\\Program Files (x86)\\ffmpeg\\bin\\ffprobe.exe",
        L"C:\\Windows\\ffprobe.exe",
        L"/opt/homebrew/bin/ffprobe",
        L"ffprobe"
    };

    for (const auto& path : hardcodedPaths) {
#ifdef _WIN32
        DWORD fileAttr = GetFileAttributesW(path.c_str());
        if (fileAttr != INVALID_FILE_ATTRIBUTES && !(fileAttr & FILE_ATTRIBUTE_DIRECTORY)) {
            // std::wcerr << L"Found ffprobe at: " << path << std::endl;
            return path;
        }
#else
        FILE* file = fopen(path.c_str(), "r");
        if (file) {
            fclose(file);
            return path;
        }
#endif
    }

    return L"ffprobe.exe";
}

int getVideoDuration(const std::wstring& filename) {
    std::wstring ffprobePath = findFfprobe();
    std::wstring cmd = L"" + ffprobePath + L" -v error -show_entries format=duration -of json " + filename + L"";
    std::string output = execCommand(cmd);

    if (output.empty()) {
        std::cerr << "Error: Could not execute ffprobe.exe" << std::endl;
        return -1;
    }

    double duration = extractValueFromJson(output, "duration");
    if (duration < 0) {
        std::cerr << "Error: Could not parse duration from ffprobe output" << std::endl;
        return -1;
    }

    return static_cast<int>(std::round(duration));
}

double getVideoBitrate(const std::wstring& filename) {
    std::wstring ffprobePath = findFfprobe();
    std::wstring cmd = L"" + ffprobePath + L" -v error -show_entries format=bit_rate -of json " + filename + L"";
    std::string output = execCommand(cmd);

    if (output.empty()) {
        std::cerr << "Error: Could not execute ffprobe.exe" << std::endl;
        return -1.0;
    }

    int bitrate = extractValueFromJson(output, "bit_rate");
    if (bitrate < 0) {
        std::cerr << "Error: Could not parse bitrate from ffprobe output" << std::endl;
        return -1.0;
    }

    return bitrate / 1000;
}

int parseTimeToSeconds(const std::wstring& time) {
    std::vector<int> parts;
    std::wstringstream ss(time);
    std::wstring segment;

    while (std::getline(ss, segment, L':')) {
        try {
            parts.push_back(std::stoi(segment));
        } catch (...) {
            return -1;
        }
    }

    if (parts.empty() || parts.size() > 3) {
        return -1;
    }

    int seconds = 0;

    if (parts.size() == 1) {
        seconds = parts[0];
    } else if (parts.size() == 2) {
        seconds = parts[0] * 60 + parts[1];
    } else if (parts.size() == 3) {
        seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    }

    return seconds;
}

#ifdef _WIN32
std::wstring displayText;
std::wstring windowTitle;
HWND hEdit;

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
        case WM_CREATE: {
            HFONT hFont = CreateFontW(24, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                                     DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                     DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Segoe UI");

            hEdit = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
                                   WS_CHILD | WS_VISIBLE | ES_CENTER | ES_READONLY,
                                   20, 20, 260, 40, hwnd, (HMENU)1, NULL, NULL);
            SendMessageW(hEdit, WM_SETFONT, (WPARAM)hFont, TRUE);
            SetWindowTextW(hEdit, displayText.c_str());

            CreateWindowW(L"BUTTON", L"Copy to Clipboard",
                        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                        70, 80, 160, 35, hwnd, (HMENU)2, NULL, NULL);
            return 0;
        }

        case WM_COMMAND: {
            if (LOWORD(wParam) == 2) {
                if (OpenClipboard(hwnd)) {
                    EmptyClipboard();
                    HGLOBAL hClipboardData = GlobalAlloc(GMEM_MOVEABLE, (displayText.size() + 1) * sizeof(wchar_t));
                    if (hClipboardData) {
                        wchar_t* pchData = (wchar_t*)GlobalLock(hClipboardData);
                        wcscpy(pchData, displayText.c_str());
                        GlobalUnlock(hClipboardData);
                        SetClipboardData(CF_UNICODETEXT, hClipboardData);
                    }
                    CloseClipboard();
                    SendMessageW(hwnd, WM_CLOSE, 0, 0);
                    // MessageBoxW(hwnd, L"Copied to clipboard!", L"Success", MB_OK | MB_ICONINFORMATION);
                }
            }
            return 0;
        }

        case WM_CLOSE:
            DestroyWindow(hwnd);
            return 0;

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

void showGuiWindow(const std::wstring& value, const std::wstring& title) {
    displayText = value;
    windowTitle = title;

    WNDCLASS wc = {};
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = TEXT("DurationWindow");
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);

    RegisterClass(&wc);

    HWND hwnd = CreateWindowExW(0, L"DurationWindow", windowTitle.c_str(),
                               WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
                               CW_USEDEFAULT, CW_USEDEFAULT, 320, 180,
                               NULL, NULL, GetModuleHandle(NULL), NULL);

    if (hwnd == NULL) {
        return;
    }

    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    MSG msg = {};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
}
#endif

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::wcerr << L"Usage: dur [--bitrate] [HH:[MM:]]SS or video_file.{avi,mp4,webm,mkv} [--gui]" << std::endl;
#ifdef _WIN32
        std::wcerr << L"_WIN32" << std::endl;
#else
        std::wcerr << L"not _WIN32" << std::endl;
#endif
        return 1;
    }

    bool bitrateMode = false;
    bool guiMode = false;
    std::wstring input;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--bitrate") {
            bitrateMode = true;
        } else if (arg == "--gui") {
            guiMode = true;
        } else {
            std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;
            input = converter.from_bytes(arg);
        }
    }

    if (input.empty()) {
        std::cerr << "Error: No input file or time specified" << std::endl;
        return 1;
    }

    if (isVideoFile(input)) {
        if (bitrateMode) {
            double bitrate = getVideoBitrate(input);
            if (bitrate < 0) {
                return 1;
            }

            std::wostringstream oss;
            oss << bitrate;
            std::wstring bitrateStr = oss.str();

#ifdef _WIN32
            if (guiMode) {
                showGuiWindow(bitrateStr, L"Video Bitrate (Kb/s)");
            } else {
                std::wcout << bitrateStr << std::endl;
            }
#else
            std::wcout << bitrateStr << std::endl;
#endif
        } else {
            int totalSeconds = getVideoDuration(input);
            if (totalSeconds < 0) {
                return 1;
            }

#ifdef _WIN32
            if (guiMode) {
                showGuiWindow(std::to_wstring(totalSeconds), L"Video Duration (seconds)");
            } else {
                std::wcout << totalSeconds << std::endl;
            }
#else
            std::wcout << totalSeconds << std::endl;
#endif
        }
    } else {
        int totalSeconds = parseTimeToSeconds(input);
        if (totalSeconds < 0) {
            std::cerr << "Invalid time format. Use [HH:[MM:]]SS" << std::endl;
            return 1;
        }
        std::cout << totalSeconds << std::endl;
    }

    return 0;
}

