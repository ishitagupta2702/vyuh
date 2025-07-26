import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold text-center mb-8">
        Welcome to Vyuh
      </h1>
      <p className="text-xl text-center mb-8">
        AI-Powered Publishing Platform
      </p>
      <div className="flex gap-4">
        <Link
          href="/api/graphql"
          className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
        >
          GraphQL Playground
        </Link>
      </div>
    </div>
  );
}
