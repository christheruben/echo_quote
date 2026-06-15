import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export async function exportQuotePdf(element: HTMLElement, fileName = "quote.pdf") {
  if (!element) return;

  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#ffffff",
    onclone: (doc) => {
      // optional safety pass to avoid weird CSS issues
      const all = doc.querySelectorAll("*");

      all.forEach((el) => {
        const node = el as HTMLElement;

        // force fallback-safe rendering
        if (node.style) {
          node.style.color = node.style.color || "#111827";
        }
      });
    },
  });

  const imgData = canvas.toDataURL("image/png");

  const pdf = new jsPDF("p", "mm", "a4");

  const pageWidth = 210;
  const pageHeight = 297;

  const imgHeight = (canvas.height * pageWidth) / canvas.width;

  let heightLeft = imgHeight;
  let position = 0;

  pdf.addImage(imgData, "PNG", 0, position, pageWidth, imgHeight);
  heightLeft -= pageHeight;

  while (heightLeft > 0) {
    position = heightLeft - imgHeight;
    pdf.addPage();
    pdf.addImage(imgData, "PNG", 0, position, pageWidth, imgHeight);
    heightLeft -= pageHeight;
  }

  pdf.save(fileName);
}