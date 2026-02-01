This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

This app is ready to deploy on Vercel.

### Option A: Deploy from this folder (eyerounds-next)

1. **Push your code to GitHub** (if not already).

2. **Go to [vercel.com/new](https://vercel.com/new)** and import your repository.

3. **Set Root Directory:**  
   In project settings, set **Root Directory** to `eyerounds-next` (because the Next.js app lives in that subfolder). Click **Edit** next to Root Directory and enter `eyerounds-next`.

4. **Environment variable (for oral boards / treatment API):**  
   In Project → Settings → Environment Variables, add:
   - **Name:** `OPENAI_API_KEY`  
   - **Value:** your OpenAI API key  
   (Only needed if you use the “Get oral boards treatment” feature.)

5. Click **Deploy**. Vercel will run `npm install` and `npm run build` in `eyerounds-next`.

### Option B: Deploy from the command line

From the repo root:

```bash
cd eyerounds-next
npx vercel
```

When prompted for the root directory, confirm it’s `eyerounds-next` (or run `npx vercel` from inside `eyerounds-next`). Add `OPENAI_API_KEY` in the Vercel dashboard under Project → Settings → Environment Variables.

---

The flashcards data is in `public/flashcards.json` and is deployed with the app. No database is required for the basic flashcard UI.
