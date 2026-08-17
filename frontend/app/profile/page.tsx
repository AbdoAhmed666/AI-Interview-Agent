"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import CVUploader from "@/components/profile/CVUploader";
import { getMyCV, getCVAnalysis } from "@/services/cv.service";

type Analysis={skills:string[];frameworks:string[];databases:string[];projects:string[];recommended_roles:string[]};
const label=(value:string)=>value.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
function Chips({items}:{items:string[]}){return items.length?<div className="mt-3 flex flex-wrap gap-2">{items.map(item=><span className="chip" key={item}>{label(item)}</span>)}</div>:<p className="muted mt-3 text-sm">No information detected yet.</p>}

export default function ProfilePage(){
 const [cv,setCv]=useState<{active_cv?:string;versions?:string[]}|null>(null);const [analysis,setAnalysis]=useState<Analysis|null>(null);const [loading,setLoading]=useState(true);
 async function refresh(){setLoading(true);try{const [c,a]=await Promise.all([getMyCV(),getCVAnalysis()]);setCv(c);setAnalysis(a)}catch(err){console.error("Failed to fetch CV",err)}finally{setLoading(false)}}
 useEffect(()=>{refresh()},[]);
 return <AppLayout><section className="mb-8"><p className="eyebrow">Candidate profile</p><h1 className="page-title mt-2">CV intelligence</h1><p className="muted mt-2">Keep your technical profile current for personalized interview questions.</p></section>
 <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]"><div className="space-y-6"><div className="panel p-6"><CVUploader onUploaded={refresh}/></div><div className="panel p-6"><p className="eyebrow">Active CV</p><h2 className="mt-2 text-xl font-bold">{loading?"Loading profile…":cv?.active_cv??"No CV uploaded"}</h2><p className="muted mt-2 text-sm">{cv?.active_cv?`${cv.versions?.length??1} uploaded version${(cv?.versions?.length??1)===1?"":"s"}`:"Upload a PDF to unlock personalized role matching."}</p></div></div>
 <div className="panel p-6"><p className="eyebrow">Role recommendations</p><h2 className="mt-2 text-xl font-bold">Where your CV fits best</h2><div className="mt-5 space-y-3">{analysis?.recommended_roles?.length?analysis.recommended_roles.map((role,index)=><div className="rounded-xl border border-[var(--border)] bg-black/10 p-4" key={role}><div className="flex items-center justify-between"><span className="font-semibold">{label(role)}</span><span className="chip">Top {index+1}</span></div></div>):<p className="muted text-sm">Upload and analyze a CV to see recommended roles.</p>}</div></div></div>
 <section className="panel mt-6 p-6"><p className="eyebrow">Extracted technical profile</p><h2 className="mt-2 text-xl font-bold">Skills and experience signals</h2><div className="mt-6 grid gap-6 md:grid-cols-2"><div><h3 className="font-semibold">Detected skills</h3><Chips items={analysis?.skills??[]}/></div><div><h3 className="font-semibold">Frameworks</h3><Chips items={analysis?.frameworks??[]}/></div><div><h3 className="font-semibold">Databases</h3><Chips items={analysis?.databases??[]}/></div><div><h3 className="font-semibold">Projects</h3><Chips items={analysis?.projects??[]}/></div></div></section></AppLayout>
}
