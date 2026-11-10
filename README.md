# Aaquib Tanweer — Portfolio

A static Jekyll portfolio with a retro desktop interface.

## Update the portfolio

- Edit `_data/portfolio.json` for the bio, headline, skills, education, experience, expertise, and projects.
- Edit `_data/services.json` for freelance service titles, descriptions, technologies, and included work.
- Edit `index.html` for the display name, role, social links, and contact details.
- Edit the `profile` object in `app.js` for contact and social actions.
- Replace `assets/profile.png` to change the profile picture.
- Edit `_config.yml` for site metadata and hosting settings.

## Develop and build

Run `npm ci`, then `npm start` (or `npm run dev`) to preview at http://127.0.0.1:3000 using Node.js 20.11 or newer. Local preview renders the Liquid templates and reads `_data/portfolio.json` without Ruby.

For the Jekyll production build, install Ruby 3.3 and run `gem install bundler -v 2.5.22` and `bundle install`, then `npm run build:site` to generate `_site`. `npm run dev:jekyll` runs the Jekyll preview.

Run `npm test` and `python3 -m unittest discover -s tests -p "test_*.py"` to check content rendering and deployment paths.

GitHub Pages deployment runs through `.github/workflows/pages.yml`.

Vercel deployment uses `vercel.json` to run `npm run build:vercel` and publish `_site`. This Node.js build renders the Liquid templates with root-relative URLs and requires no Ruby installation. Run `npm run build:vercel` locally to verify the deployment output. Redeploy on Vercel after pushing these files.
