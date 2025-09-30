import Header from './components/header';
import Submission from './components/submission';
import Hero from './components/hero';

export default function Home() {
  return (
    <div className=" min-h-screen  
    bg-[url('/blob.png')] 
    bg-no-repeat bg-right-top 
    bg-[length:80%_auto] 
    "
     style={{ backgroundSize: "cover" }} >
    <Header />

    <Hero />

    <Submission />
    </div>
  );
}

// Some comment 