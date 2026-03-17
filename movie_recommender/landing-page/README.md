# CINE-M-AURA Landing Page

A modern, responsive landing page for the CINE-M-AURA movie recommendation platform.

## Features Added

### SEO & Performance
- ✅ **Meta Tags** - Comprehensive SEO meta tags
- ✅ **Open Graph** - Facebook & social media sharing optimization
- ✅ **Twitter Cards** - Enhanced Twitter sharing
- ✅ **Schema.org** - Structured data for search engines
- ✅ **Sitemap** - XML sitemap for search engine crawling
- ✅ **Robots.txt** - Search engine crawler instructions
- ✅ **Canonical URLs** - Proper URL canonicalization

### User Experience
- ✅ **Loading Spinner** - Smooth page load experience
- ✅ **Cookie Consent** - GDPR-compliant cookie banner
- ✅ **Back to Top Button** - Easy navigation
- ✅ **Smooth Scrolling** - Enhanced navigation experience
- ✅ **Mobile Menu** - Responsive navigation
- ✅ **404 Page** - Custom error page
- ✅ **Animations** - Smooth scroll animations and transitions

### Accessibility
- ✅ **ARIA Labels** - Screen reader support
- ✅ **Keyboard Navigation** - Full keyboard accessibility
- ✅ **Focus Styles** - Visible focus indicators
- ✅ **Reduced Motion** - Respects user preferences

### Progressive Web App
- ✅ **Web Manifest** - PWA capabilities
- ✅ **Theme Colors** - Branded app experience
- ✅ **Favicon** - Professional branding

### Performance
- ✅ **Resource Preloading** - Faster initial load
- ✅ **Lazy Loading** - Optimized image loading
- ✅ **GZIP Compression** - Reduced file sizes
- ✅ **Browser Caching** - Improved repeat visits

### Security
- ✅ **Security Headers** - XSS, clickjacking protection
- ✅ **Content Security** - Safe content loading

## Project Structure

```
landing-page/
├── src/
│   ├── index.html          # Main HTML file with SEO tags
│   ├── styles/
│   │   └── main.css        # Complete stylesheet with animations
│   └── scripts/
│       └── main.js         # Interactive JavaScript features
├── 404.html                # Custom 404 error page
├── robots.txt              # SEO crawler instructions
├── sitemap.xml             # Site structure for SEO
├── manifest.json           # PWA manifest
├── .htaccess              # Server configuration (Apache)
├── package.json            # Project metadata
└── README.md              # This file
```

## Setup Instructions

### Quick Start

1. Open `src/index.html` in your web browser to view the landing page

### Development Server

For a better development experience, use a local server:

**Using Python:**
```bash
cd movie_recommender/landing-page
python -m http.server 8000
```
Then visit: `http://localhost:8000/src/index.html`

**Using Node.js (http-server):**
```bash
npx http-server . -p 8000
```

**Using VS Code Live Server:**
Right-click on `index.html` → "Open with Live Server"

## Customization Guide

### 1. Update URLs
Replace `https://movie-recommender.onrender.com/` with your actual domain in:
- `src/index.html` (meta tags, canonical URL)
- `sitemap.xml` (all URL entries)
- `manifest.json` (start_url)

### 2. Add Analytics
Uncomment and configure Google Analytics in `src/index.html`:
```javascript
// Replace 'GA_MEASUREMENT_ID' with your actual ID
gtag('config', 'YOUR-GA-ID');
```

### 3. Customize Colors
Update CSS variables in `src/styles/main.css`:
```css
:root {
    --primary-color: #6366f1;    /* Your brand color */
    --primary-dark: #4f46e5;     /* Darker shade */
    --secondary-color: #ec4899;  /* Accent color */
}
```

### 4. Replace Branding
- Add your logo in place of the emoji (🎬)
- Create actual favicon images and update the `<link>` tags
- Update `manifest.json` with real icon images

### 5. Content Updates
Edit the text content in `src/index.html`:
- Hero section title and subtitle
- Features descriptions
- Testimonials
- Call-to-action text

## Features Overview

### Navigation
- Fixed navbar with smooth scrolling
- Mobile-responsive hamburger menu
- Active link highlighting

### Hero Section
- Animated gradient background
- Call-to-action buttons
- Statistics counters with animations

### Sections
- **Features:** 6 key features in a responsive grid
- **How It Works:** 3-step process explanation
- **Testimonials:** User reviews carousel
- **CTA:** Email signup form with validation

### Interactive Elements
- Form validation with error messages
- Notification system for user feedback
- Parallax scrolling effects
- Intersection observer animations

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome  | Latest  |
| Firefox | Latest  |
| Safari  | Latest  |
| Edge    | Latest  |
| Mobile  | iOS 12+, Android 5+ |

## Performance Metrics

Target performance scores:
- Lighthouse Performance: 95+
- SEO: 100
- Accessibility: 95+
- Best Practices: 100

## Deployment

This landing page is ready to deploy to:
- GitHub Pages
- Netlify
- Vercel
- Render (already configured)
- Any static hosting service

Simply upload the entire `landing-page` folder to your hosting provider.

## Troubleshooting

**Issue:** Cookie banner not showing
- Check localStorage: `localStorage.getItem('cookieConsent')`
- Clear localStorage: `localStorage.clear()`

**Issue:** Animations not working
- Check if user has "Reduce Motion" enabled in OS settings
- Verify JavaScript console for errors

**Issue:** Mobile menu not toggling
- Ensure JavaScript is enabled
- Check browser console for errors

## Contributing

Feel free to customize and improve this landing page for your specific needs.

## License

MIT License - Feel free to use this template for any project.
