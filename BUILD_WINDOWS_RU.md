# Сборка CV Builder для Windows

## Требования

- Windows 10 или 11, 64-bit;
- Python 3.12 x64;
- Inno Setup 6;
- PowerShell;
- интернет при первой установке Python-зависимостей.

Windows SDK нужен только для цифровой подписи. Для обычной локальной сборки
он не требуется.

## Подготовка

Откройте PowerShell в папке проекта:

```powershell
cd C:\path\to\cv_desktop_app
python -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
```

Если PowerShell запрещает активацию виртуального окружения, один раз выполните:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Сборка

```powershell
.\build_windows.ps1
```

Скрипт автоматически:

1. создает многоразмерную `assets\CVBuilder.ico`;
2. собирает `CVBuilder.exe` через PyInstaller;
3. добавляет версию 1.2.3 и иконку в EXE;
4. создает установщик через Inno Setup 6.

Готовый файл:

```text
installer\CVBuilder-Windows-Setup.exe
```

Именно этот файл нужно передавать пользователям. Python и библиотеки им
устанавливать не нужно — они находятся внутри приложения.

## Проверка перед раздачей

1. Установите `CVBuilder-Windows-Setup.exe` на чистой Windows 10/11.
2. Проверьте запуск из меню «Пуск» и ярлыка.
3. Создайте CV, закройте и снова откройте приложение — данные должны сохраниться.
4. Проверьте экспорт PDF, экспорт JSON и повторный импорт JSON.
5. Проверьте удаление приложения через Windows Settings → Apps.

## Подпись для публичного релиза

Без подписи установщик работает, но Windows SmartScreen может показать
предупреждение. Для подписи установите Windows SDK и передайте скрипту:

```powershell
$env:WINDOWS_PFX_BASE64 = "<PFX certificate encoded as Base64>"
$env:WINDOWS_PFX_PASSWORD = "<certificate password>"
.\build_windows.ps1
```

Скрипт подпишет и `CVBuilder.exe`, и итоговый установщик с SHA-256 timestamp.

