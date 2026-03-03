"use client"

import { useEffect } from "react"
import { usePathname } from "next/navigation"
import { connectMarketWS } from "../services/wsService"

interface Props {
  children: React.ReactNode
}

export default function ServiceInitializer({ children }: Props) {

  const pathname = usePathname()

  useEffect(() => {
    connectMarketWS()
  }, [pathname])

  return <>{children}</>
}
