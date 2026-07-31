# GitHub Actions — настройка сборки CV Builder

## Что делает workflow

Файл `.github/workflows/build-installers.yml` описывает автоматическую сборку
трех установщиков на виртуальных компьютерах GitHub:

| Runner | Архитектура | Результат |
|---|---:|---|
| `macos-14` | Apple Silicon, arm64 | `CVBuilder-macOS-AppleSilicon.dmg` |
| `macos-15-intel` | Intel, x64 | `CVBuilder-macOS-Intel.dmg` |
| `windows-2022` | Intel/AMD, x64 | `CVBuilder-Windows-Setup.exe` |

GitHub создает чистую виртуальную машину для каждого job, загружает код,
устанавливает Python 3.12 и зависимости, запускает тесты и скрипт сборки, после
чего сохраняет установщик как **Artifact**. Runner `macos-15-intel` является
актуальной поддерживаемой меткой GitHub на момент подготовки инструкции.

Официальная документация:

- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Управление workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs)
- [Workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)

## 1. Создать репозиторий

Создайте пустой репозиторий на GitHub. Папка `cv_desktop_app` должна стать
корнем репозитория: каталог `.github` обязан находиться непосредственно в
корне, иначе GitHub не обнаружит workflow.

На Mac выполните:

```bash
cd /Users/playrix/Documents/CV/cv_desktop_app
git init
git add .
git commit -m "Initial CV Builder release"
git branch -M main
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

Замените `OWNER/REPOSITORY` на владельца и имя созданного репозитория. Для
приватного репозитория GitHub может запросить Personal Access Token или
настроенный SSH-доступ.

Перед commit убедитесь, что добавлен `CVBuilder.spec`:

```bash
git status --short
```

Готовые `build`, `dist`, `installer` и DMG коммитить не нужно.

## 2. Разрешить GitHub Actions

Откройте репозиторий:

1. **Settings → Actions → General**.
2. В **Actions permissions** разрешите использование GitHub Actions.
3. Сохраните настройки.
4. Перейдите на вкладку **Actions**.

В списке должен появиться workflow **Build desktop installers**.

## 3. Первая сборка без сертификатов

Для тестовой сборки secrets не нужны:

1. **Actions → Build desktop installers**.
2. Нажмите **Run workflow**.
3. Выберите ветку `main`.
4. Еще раз нажмите **Run workflow**.

Параллельно запустятся macOS Apple Silicon, macOS Intel и Windows jobs. Зеленая
галочка означает успешную сборку.

Внизу страницы завершенного run появится раздел **Artifacts**:

- `CVBuilder-macOS-AppleSilicon`;
- `CVBuilder-macOS-Intel`;
- `CVBuilder-Windows`.

Каждый artifact скачивается как ZIP. Внутри находится соответствующий DMG или
EXE. В текущем workflow artifacts хранятся 14 дней.

Такие сборки функциональны, но Windows SmartScreen и macOS Gatekeeper могут
показывать предупреждение, потому что публичная цифровая подпись не настроена.

## 4. Автоматическая сборка по тегу

Workflow автоматически запускается для тегов, начинающихся с `v`:

```bash
git tag -a v1.2.3 -m "CV Builder 1.2.3"
git push origin v1.2.3
```

Перед созданием следующего тега синхронизируйте номер версии в:

- `CVBuilder.spec`;
- `packaging/windows-version-info.txt`;
- `packaging/windows-installer.iss`.

Workflow сохраняет файлы как artifacts, но не создает GitHub Release
автоматически. Для релиза скачайте три artifacts, создайте **Releases → Draft a
new release** и прикрепите DMG/EXE вручную.

## 5. Secrets для подписи macOS

Для распространения без предупреждений Gatekeeper нужны участие в Apple
Developer Program, сертификат **Developer ID Application** и нотарификация
Apple.

Добавьте secrets через **Settings → Secrets and variables → Actions → New
repository secret**:

| Secret | Содержимое |
|---|---|
| `MACOS_CERTIFICATE_B64` | экспортированный `.p12` сертификат в Base64 |
| `MACOS_CERTIFICATE_PASSWORD` | пароль `.p12` |
| `MACOS_KEYCHAIN_PASSWORD` | временный сложный пароль для CI-keychain |
| `APPLE_SIGN_IDENTITY` | полное имя `Developer ID Application: ... (TEAMID)` |
| `APPLE_ID` | Apple ID разработчика |
| `APPLE_TEAM_ID` | Team ID из Apple Developer account |
| `APPLE_APP_PASSWORD` | app-specific password для Apple ID |

Экспортируйте Developer ID Application вместе с private key из Keychain
Access в файл `DeveloperID.p12`, затем на Mac скопируйте Base64:

```bash
base64 -i DeveloperID.p12 | tr -d '\n' | pbcopy
```

Вставьте результат в `MACOS_CERTIFICATE_B64`. Сам `.p12` и его пароль нельзя
коммитить в Git.

Когда все macOS-secrets заданы, workflow:

1. создает временный keychain;
2. импортирует сертификат;
3. подписывает `.app` с hardened runtime;
4. создает DMG;
5. отправляет DMG в Apple через `notarytool`;
6. прикрепляет notarization ticket через `stapler`.

Подробнее: [Apple — Signing apps with Developer ID](https://developer.apple.com/developer-id/).

## 6. Secrets для подписи Windows

Добавьте два repository secret:

| Secret | Содержимое |
|---|---|
| `WINDOWS_PFX_BASE64` | Windows code-signing `.pfx` в Base64 |
| `WINDOWS_PFX_PASSWORD` | пароль сертификата |

В PowerShell можно скопировать Base64 так:

```powershell
[Convert]::ToBase64String(
    [IO.File]::ReadAllBytes("C:\path\code-signing.pfx")
) | Set-Clipboard
```

При наличии secrets `build_windows.ps1` подписывает и `CVBuilder.exe`, и
итоговый установщик с SHA-256 timestamp. Без secrets Windows SDK не нужен.

GitHub хранит secrets в зашифрованном виде и передает их только workflow,
который явно ссылается на них. Не выводите secrets в лог и не храните
сертификаты в репозитории:
[GitHub Actions secrets](https://docs.github.com/en/actions/concepts/security/secrets).

## 7. Что раздавать пользователям

После проверки раздавайте только:

- `CVBuilder-macOS-AppleSilicon.dmg`;
- `CVBuilder-macOS-Intel.dmg`;
- `CVBuilder-Windows-Setup.exe`.

Папки `build`, `dist`, исходный код, сертификаты и файлы JSON пользователям не
нужны.

## Частые проблемы

### Workflow не появился во вкладке Actions

- `.github/workflows/build-installers.yml` не находится в корне репозитория;
- файл не отправлен в ветку `main`;
- GitHub Actions запрещены в настройках репозитория.

### macOS build сообщает о старой версии Tk

Job использует не тот Python. Убедитесь, что `actions/setup-python` выполняется
до установки зависимостей и задан `python-version: "3.12"`.

### Не найден `CVBuilder.spec`

Проверьте, что он добавлен в Git. В текущем `.gitignore` для него уже сделано
исключение `!CVBuilder.spec`.

### Подпись или нотарификация macOS завершилась ошибкой

- проверьте пароль `.p12`;
- убедитесь, что экспортирован private key;
- проверьте точное значение `APPLE_SIGN_IDENTITY`;
- проверьте Team ID и app-specific password;
- откройте log шага `notarytool`.

### Установщик собран, но Windows показывает SmartScreen

Сборка не подписана доверенным code-signing сертификатом либо сертификат еще
не имеет достаточной репутации SmartScreen.

