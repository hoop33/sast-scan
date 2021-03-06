# Introduction

```bash
  ___            _____ _                    _
 / _ \          |_   _| |                  | |
/ /_\ \_ __  _ __ | | | |__  _ __ ___  __ _| |_
|  _  | '_ \| '_ \| | | '_ \| '__/ _ \/ _` | __|
| | | | |_) | |_) | | | | | | | |  __/ (_| | |_
\_| |_/ .__/| .__/\_/ |_| |_|_|  \___|\__,_|\__|
      | |   | |
      |_|   |_|
```

This repo builds `appthreat/sast-scan` (and `quay.io/appthreat/sast-scan`), a container image with a number of bundled open-source static analysis security testing (SAST) tools. This is like a Swiss Army knife for DevSecOps engineers.

[![Docker Repository on Quay](https://quay.io/repository/appthreat/sast-scan/status "Docker Repository on Quay")](https://quay.io/repository/appthreat/sast-scan)

## Features

- No messy configuration and no server required
- Scanning is performed directly in the CI and is extremely quick. Full scan often takes only couple of minutes
- Gorgeous [HTML](http://htmlpreview.github.io/?https://github.com/AppThreat/sast-scan/blob/master/docs/findsecbugs-report.html) [reports](http://htmlpreview.github.io/?https://github.com/AppThreat/sast-scan/blob/master/docs/pmd-report.html) that you can proudly share with your colleagues, and the security team
- Automatic exit code 1 (build breaker) with critical and high vulnerabilities
- There are a number of small things that will bring a smile to any DevOps team

## Bundled tools

| Programming Language | Tools                              |
| -------------------- | ---------------------------------- |
| ansible              | ansible-lint                       |
| apex                 | pmd                                |
| aws                  | cfn-lint, cfn_nag                  |
| bash                 | shellcheck                         |
| bom                  | cdxgen                             |
| credscan             | gitleaks                           |
| depscan              | dep-scan                           |
| go                   | gosec, staticcheck                 |
| java                 | cdxgen, gradle, find-sec-bugs, pmd |
| jsp                  | pmd                                |
| json                 | jq, jsondiff, jsonschema           |
| kotlin               | detekt                             |
| kubernetes           | kube-score                         |
| nodejs               | cdxgen, NodeJsScan, eslint, yarn   |
| puppet               | puppet-lint                        |
| plsql                | pmd                                |
| python               | bandit, cdxgen, pipenv             |
| ruby                 | cyclonedx-ruby                     |
| rust                 | cdxgen, cargo-audit                |
| terraform            | tfsec                              |
| Visual Force (vf)    | pmd                                |
| Apache Velocity (vm) | pmd                                |
| yaml                 | yamllint                           |

## Bundled languages/runtime

- jq
- Go 1.12
- Python 3.6
- OpenJDK 11 (jre)
- Ruby 2.5.5
- Rust
- Node.js 10
- Yarnpkg

Some reports get converted into an open-standard called [SARIF](https://sarifweb.azurewebsites.net/). Please see the section on `Viewing reports` for various viewer options for this.

### Tools enabled for SARIF conversion

- Bash - shellcheck
- Credscan - gitleaks
- Python - bandit
- Node.js - NodeJsScan
- pmd, find-sec-bugs
- Go - gosec, staticcheck
- Terraform - tfsec

## Usage

sast-scan is ideal for use with CI and also as a pre-commit hook for local development.

## Integration with Azure DevOps

Refer to the [document](docs/azure-devops.md)

## Integration with GitHub action

This tool can be used with GitHub actions using this [action](https://github.com/marketplace/actions/sast-scan). All the supported languages can be used.

This repo self-tests itself with sast-scan! Check the GitHub [workflow file](https://github.com/AppThreat/sast-scan/blob/master/.github/workflows/pythonapp.yml) of this repo.

```yaml
- name: Self sast-scan
  uses: AppThreat/sast-scan-action@v1.0.0
  with:
    output: reports
    type: python,bash
- name: Upload scan reports
  uses: actions/upload-artifact@v1.0.0
  with:
    name: sast-scan-reports
    path: reports
```

## Integration with Google CloudBuild

Use this [custom builder](https://github.com/CloudBuildr/google-custom-builders/tree/master/sast-scan) to add sast-scan as a build step.

The full steps are reproduced below.

1. Add the custom builder to your project

```bash
git clone https://github.com/CloudBuildr/google-custom-builders.git
cd google-custom-builders/sast-scan
gcloud builds submit --config cloudbuild.yaml .
```

2. Use it in cloudbuild.yaml

```yaml
steps:
  - name: "gcr.io/$PROJECT_ID/sast-scan"
    args: ["--type", "python"]
```

## Integration with CircleCI

Refer to the [document](docs/circleci.md)

## Custom integration

SARIF reports produced by sast-scan can be integrated with other compatible tools. It can also be easily imported into databases such as BigQuery for visualization purposes. Refer to [integration](docs/integration.md) document for detailed explanation on the SARIF format.

### Scanning projects locally

Scan python project

```bash
docker run --rm -e "WORKSPACE=${PWD}" -v "$PWD:/app:cached" quay.io/appthreat/sast-scan scan --src /app --type python
```

On Windows the command changes slightly depending on the terminal.

cmd
```
docker run --rm -e "WORKSPACE=%cd%" -e "GITHUB_TOKEN=%GITHUB_TOKEN%" -v "%cd%:/app:cached" quay.io/appthreat/sast-scan scan
```

powershell and powershell core
```
docker run --rm -e "WORKSPACE=$(pwd)" -e "GITHUB_TOKEN=$env:GITHUB_TOKEN" -v "$(pwd):/app:cached" quay.io/appthreat/sast-scan scan
```

WSL bash
```
docker run --rm -e "WORKSPACE=${PWD}" -e "GITHUB_TOKEN=${GITHUB_TOKEN}" -v "$PWD:/app:cached" quay.io/appthreat/sast-scan scan 
```

git-bash
```
docker run --rm -e "WORKSPACE=${PWD}" -e "GITHUB_TOKEN=${GITHUB_TOKEN}" -v "/$PWD:/app:cached" quay.io/appthreat/sast-scan scan 
```

Don't forget the slash (/) before $PWD for git-bash!

Scan multiple projects

```bash
docker run --rm -e "WORKSPACE=${PWD}" -v "$PWD:/app:cached" quay.io/appthreat/sast-scan scan --src /app --type credscan,nodejs,python,yaml --out_dir /app/reports
```

Scan java project

For java and jvm language based projects, it is important to compile the projects before invoking sast-scan in the dev and CI workflow.

```bash
docker run --rm -e "WORKSPACE=${PWD}" -v ~/.m2:/.m2 -v <source path>:/app quay.io/appthreat/sast-scan scan --src /app --type java

# For gradle project
docker run --rm -e "WORKSPACE=${PWD}" -v ~/.gradle:/.gradle -v <source path>:/app quay.io/appthreat/sast-scan scan --src /app --type java
```

Scan python project (Without any telemetry)

```bash
docker run --rm -e "WORKSPACE=${PWD}" -e "DISABLE_TELEMETRY=true" -v $PWD:/app quay.io/appthreat/sast-scan scan --src /app --type python
```

**Automatic project detection**

Feel free to skip `--type` to enable auto-detection. Or pass comma-separated values if the project has multiple types.

### Invoking built-in tools

Bandit

```bash
docker run --rm -v <source path>:/app quay.io/appthreat/sast-scan bandit -r /app
```

## Viewing reports

Reports would be produced in the directory specified for `--out_dir`. In the above examples, it is set to `reports` which will be a directory under the source code root directory.

Some of the reports would be converted to a standard called [SARIF](https://sarifweb.azurewebsites.net/). Such reports would end with the extension `.sarif`. To open and view the sarif files require a viewer such as:

- Online viewer - http://sarifviewer.azurewebsites.net/
- VS Code extension - https://marketplace.visualstudio.com/items?itemName=MS-SarifVSCode.sarif-viewer
- Visual Studio extension - https://marketplace.visualstudio.com/items?itemName=WDGIS.MicrosoftSarifViewer
- Azure DevOps extension - https://marketplace.visualstudio.com/items?itemName=shiftleftsecurity.sl-scan-results

**Example reports:**

Online viewer can be used to manually upload the .sarif files as shown.

![Online viewer](docs/sarif-online-viewer.png)

Azure DevOps SARIF plugin can be integrated to show the analysis integrated with the build run as shown.

![Azure DevOps integration](docs/azure-devops.png)

![Build breaker](docs/build-breaker.png)

## Alternatives

GitLab [SAST](https://docs.gitlab.com/ee/user/application_security/sast/) uses numerous single purpose [analyzers](https://gitlab.com/gitlab-org/security-products/analyzers) and Go based converters to produce a custom json format. This model has the downside of increasing build times since multiple container images should get downloaded and hence is not suitable for CI environments such as Azure Pipelines, CodeBuild and Google CloudBuild. Plus the license used by GitLab is not opensource even though the analyzers merely wrap existing oss tools!

MIR [SWAMP](https://www.mir-swamp.org/) is a free online service for running both oss and commercial static analysis for a number of languages simillar to sast-scan. There is a free SWAMP-in-a-box offering but the setup is a bit cumbersome. They use a xml format called SCARF with a number of perl based converters. SARIF, in contrast, is json based and is much easier to work with for integration and UI purposes. By adopting python, sast-scan is a bit easy to work with for customisation.

## Sponsors

AppThreat is funded and supported by [ShiftLeft](https://shiftleft.io/). For general discussions and suggestions, please feel free to use either the GitHub [issues](https://github.com/AppThreat/sast-scan/issues) or ShiftLeft [discussion forum](https://discuss.shiftleft.io/)
