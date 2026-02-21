import Head from 'next/head';
import Dashboard from '../components/Dashboard';

/**
 * StrikeIQ Front-End Entry Point
 * - Consolidated to a single source of truth in Dashboard
 * - Removed redundant state to prevent flicker
 */
export default function Home() {
  console.log("INDEX PAGE RENDERED");
  return (
    <>
      <Head>
        <title>StrikeIQ - Options Market Intelligence</title>
        <meta name="description" content="AI-powered options market intelligence for Indian markets" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <Dashboard />
      </main>
    </>
  );
}
