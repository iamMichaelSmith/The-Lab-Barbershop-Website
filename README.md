# The Lab Barbershop Website

Production-ready static website for **The Lab Barbershop** (Manor, TX), built with **Eleventy + Tailwind CSS**.

This project is intentionally lightweight, SEO-focused, and designed for modern static hosting on AWS.

## Highlights

- Modern, responsive UI with conversion-focused CTAs
- Local SEO foundations (metadata + structured data)
- Blog support for grooming/style content marketing
- Static-first architecture (fast load, low ops overhead)
- Deployment-ready for AWS static hosting stack

## Tech Stack

- [Eleventy (11ty)](https://www.11ty.dev/) — static site generator
- [Tailwind CSS](https://tailwindcss.com/) — utility-first styling
- PostCSS + Autoprefixer — CSS processing

## Local Development

```bash
npm install
npm run dev
```

Build production site:

```bash
npm run build
```

Generated output is in:

- `_site/`

## AWS Static Site Deployment Architecture

This site is intended to run on the following AWS services:

- **Amazon S3** — static site asset storage
- **Amazon CloudFront** — global CDN + HTTPS edge delivery
- **Amazon Route 53** — DNS + domain routing
- **AWS Certificate Manager (ACM)** — TLS certificates for custom domain
- **AWS WAF** *(recommended)* — edge protection and request filtering
- **AWS CloudWatch** *(recommended)* — observability for edge/app metrics

### Typical Production Flow

1. Build site (`npm run build`)
2. Upload `_site/` to S3 bucket
3. Serve via CloudFront distribution
4. Map domain in Route 53
5. Attach ACM certificate for HTTPS
6. Invalidate CloudFront cache on deploy updates

## SEO + Content Strategy Notes

- Blog content is structured under `src/blogs/` for keyword-driven local search growth
- Business metadata and schema are included in the base layout
- Keep NAP (Name/Address/Phone) consistent across site and GBP

## Project Structure

```text
src/
  _includes/layouts/    # Nunjucks base templates
  assets/css/           # Tailwind source styles
  assets/js/            # Site interaction scripts
  assets/images/        # Static images + favicon
  blogs/                # Markdown blog posts
  index.njk             # Home page
  blogs.njk             # Blog index page
_site/                  # Production build output
```

## Employment-Ready Implementation Notes

This project demonstrates practical frontend and deployment skills relevant to production environments:

- Static site architecture and performance-aware delivery
- Semantic SEO implementation and metadata strategy
- Modular template structure for maintainability
- Cloud-ready deployment strategy using core AWS services
- Conversion-oriented UX decisions for local service businesses

## Booking CTA

Primary booking destination:

- https://app.thecut.co/barbers/thelab

## License

Private project for The Lab Barbershop.
