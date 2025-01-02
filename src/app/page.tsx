import Chat from '../components/Chat'

export default function Home() {
  return (
    <main className="min-h-screen p-4 bg-gray-100">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          AutoGen Chat
        </h1>
        <Chat />
      </div>
    </main>
  )
}