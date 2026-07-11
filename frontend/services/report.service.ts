import api from "@/lib/axios";

export async function downloadReport(data:any){

const response=await api.post(
"/download-report",
data,
{
responseType:"blob",
});

const url=window.URL.createObjectURL(response.data);

const link=document.createElement("a");

link.href=url;

link.download="Interview_Report.pdf";

link.click();
}