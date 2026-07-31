# CV Builder — установка, сборка и использование

## Что раздавать пользователям

- **macOS Apple Silicon:** `CVBuilder-macOS-AppleSilicon.dmg`.
- **macOS Intel:** `CVBuilder-macOS-Intel.dmg`.
- **Windows 10/11 x64:** `CVBuilder-Windows-Setup.exe`.

Текущий локальный файл `CVBuilder-macOS.dmg` собран для Apple Silicon. Два
варианта macOS создаются workflow `.github/workflows/build-installers.yml`.
Пользователям не нужны исходники, папки `build`/`dist`, Python или JSON-файлы
из проекта.

Для публичной раздачи рекомендуется подписывать Windows-инсталлятор, а
macOS-приложение — подписывать Developer ID и нотарифицировать у Apple.
Неподписанная сборка работает, но Windows SmartScreen или macOS Gatekeeper
могут показать предупреждение.

## Что требуется конечному пользователю

### Windows

1. Windows 10 или 11, 64-bit.
2. Запустить `CVBuilder-Windows-Setup.exe` и пройти обычную установку.
3. Открыть **CV Builder** через меню «Пуск» или созданный ярлык.

Python, Tk, ReportLab и остальные библиотеки уже находятся внутри приложения.
Интернет, учетная запись и отдельная база данных не требуются.

### macOS

1. Скачать DMG, соответствующий процессору Mac: Apple Silicon или Intel.
2. Открыть DMG и перетащить **CVBuilder.app** в **Applications**.
3. Запустить приложение из Applications.

Дополнительный софт не требуется. Приложение работает локально и офлайн.

## Что требуется для сборки на macOS

- macOS и Xcode Command Line Tools: `xcode-select --install`;
- Python 3.12;
- Tk 8.6 или новее; рекомендуется Tk 9.0;
- Python-зависимости из `requirements-build.txt`.

Пример подготовки через Homebrew:

```bash
brew install python@3.12 python-tk@3.12
/opt/homebrew/bin/python3.12 -m venv .venv-build
source .venv-build/bin/activate
python -m pip install -r requirements-build.txt
PYTHON_BIN=.venv-build/bin/python ./build_macos.sh
```

Результат: `CVBuilder-macOS.dmg`. Локальная сборка соответствует архитектуре
текущего Mac. Для одновременной сборки Apple Silicon и Intel используйте
GitHub Actions workflow. Пошаговая настройка описана в
`GITHUB_ACTIONS_RU.md`.

Для подписи и нотарификации дополнительно нужны Apple Developer ID certificate,
Apple ID, Team ID и app-specific password. Без них скрипт создает локальную
ad-hoc подписанную, но не нотарифицированную сборку.

## Сборка и запуск из исходников на Windows

Для запуска из исходников нужны Python 3.12 и зависимости:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Для создания инсталлятора дополнительно нужны Inno Setup 6 и зависимости
сборки:

```powershell
python -m pip install -r requirements-build.txt
.\build_windows.ps1
```

Результат: `installer\CVBuilder-Windows-Setup.exe`.

Подробная пошаговая инструкция: `BUILD_WINDOWS_RU.md`. Windows-сборка
автоматически создает `.ico`, добавляет версию и иконку в EXE, а затем
упаковывает приложение через Inno Setup.

## Используемый стек

- Python 3.12;
- Tk/Tkinter 9.0 и CustomTkinter 5.2 — desktop UI;
- ReportLab — генерация PDF;
- JSON-файлы — локальное хранение CV;
- PyInstaller — упаковка приложения;
- Inno Setup 6 — Windows-инсталлятор;
- `codesign`, `hdiutil` и DMG — macOS-упаковка;
- GitHub Actions — сборка Windows, macOS Apple Silicon и macOS Intel.

Backend, облако, аналитика и сетевые запросы отсутствуют.

## Короткая инструкция по использованию

1. На стартовом экране нажмите **+ New CV** или откройте существующее CV.
   Доступны переименование и удаление документов.
2. Заполните четыре раздела слева: **Profile**, **Summary**, **Experience** и
   **Education**. Placeholder исчезает при вводе и не попадает в CV.
3. В **Experience** добавляйте роли, редактируйте их и меняйте порядок —
   наиболее релевантную роль лучше располагать первой.
4. Изменения сохраняются автоматически на этом устройстве. Статус сохранения
   и процент заполнения отображаются в интерфейсе.
5. Нажмите **Export PDF**, чтобы получить готовое резюме.
6. **Export JSON** создает переносимую резервную копию текущего CV.
7. **Example JSON** сохраняет пример структуры: его можно отредактировать
   вручную и вернуть через **Import JSON**. Импортированный файл становится
   отдельным CV в библиотеке.
8. Кнопка **All CVs** возвращает к списку документов. Перед удалением CV
   рекомендуется экспортировать JSON — удаление необратимо.

Автосохраненные данные находятся:

- macOS: `~/Library/Application Support/CV Builder/documents`;
- Windows: `%APPDATA%\CV Builder\documents`.
