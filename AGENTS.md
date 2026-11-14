# Agent notes

Home Assistant custom integration (`custom_components/eteck`), distributed via HACS.
Validate every change with `mise run test` and `mise run lint`. Use Conventional
Commits. Never edit `CHANGELOG.md`, `.release-please-manifest.json` or the `version`
in `manifest.json`; release-please owns them.

## Adding or updating tariffs

This is the most common change. Follow these steps in order.

1. **Ask the user for the tariff sheet PDF.** You need the Eteck "Product- en
   tarievenblad" for their project and year (from the Eteck website or customer
   portal). Do not continue without it. Never take tariffs from memory, a web
   search, an invoice, or numbers the user types from memory; the PDF is the
   only accepted source.
2. **Read the PDF** and take from it: the project name exactly as printed, the
   year, and the lines under "Vaste kosten" and "Variabele kosten". Skip
   "Overige kosten". Amounts are including VAT; write them with a `.` as decimal
   separator. If the sheet has a line that is not in the key table in
   `CONTRIBUTING.md`, stop and open an issue instead (step 4b).
3. **Ask the user how they want to contribute**: are they comfortable opening a
   pull request from their GitHub account, or would they prefer to open an
   issue and let a maintainer make the change? Do not choose for them.
4. Then either:

   a. **Pull request.** Edit `custom_components/eteck/tariffs.yaml` following
      `CONTRIBUTING.md`. For a new project also add a row to the table in
      `README.md`; for a new year update that row. Run `mise run test`. Open a
      PR titled like `feat(tariffs): add <project> <year>`. In the PR body list
      the values you entered, the "Laatst gewijzigd" date on the sheet, and ask
      the user to attach the PDF to the PR in the browser so a maintainer can
      check it.

   b. **Issue.** Open an issue with the "Tariffs" template
      (`gh issue create --template tariffs.yml`, or give the user the link
      https://github.com/desyncdotdev/home-assistant-eteck-tarieven/issues/new?template=tariffs.yml).
      Fill in the project name, year and all values from the sheet, and ask the
      user to attach the PDF to the issue in the browser.

Show the user the values you read from the PDF before submitting either one, so
they can confirm them against their sheet.
