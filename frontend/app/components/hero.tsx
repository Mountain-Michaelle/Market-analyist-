import React from 'react'

const Hero = () => {
  return (
   <div className="flex justify-center items-center mt-7 px-4 md:mb-20">
  <div className="text-center max-w-[90%] md:max-w-[70%]">
    <h1 className="text-5xl text-center sm:text-6xl font-extrabold animate-pulse duration-1000 md:text-5xl lg:text-7xl bg-gradient-to-r p-2 from-black to-blue-600 bg-clip-text text-transparent">
      Know. Analyze. Decide.
    </h1>
    <p className="mt-3 text-lg sm:text-base text-blue-900 font-bold md:text-lg lg:text-xl">
      Automated market analysis delivered to inbox.  </p>
  </div>
</div>

  )
}
export default Hero;