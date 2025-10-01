import React from 'react'
import Image from 'next/image'
import Link from 'next/link'

const Header = () => {
  return (
    <div className='p-3 px-5 flex justify-between shadow-md'>
        <div className='flex font-bold gap-2 items-center'>
            <Image src={'/logo.png'} width={30} height={30} alt="" />
            <h2>TrendSight</h2>
        </div>

        <div className='flex font-bold gap-3 items-center'>
            <Link href="/dashboard">
              <button className=' p-2 rounded-md text-white'
              style={{background:"linear-gradient(83.07deg, #5200FF 6.18%, #2C86D9 97%)"}}>Dashboard</button>  
            </Link>
            
        </div>
    </div>
  )
}

export default Header