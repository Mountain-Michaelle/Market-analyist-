import React, { JSX } from 'react';

type ReportData = string | number | boolean | ReportDataObject;
interface ReportDataObject {
  emailReport: string[]  // the backend object
  isOpen: boolean;
  handleIsOpen: () => void;
}

const Report = ({ emailReport, isOpen, handleIsOpen }: ReportDataObject) => {
  if (!emailReport || !isOpen) return null;

  // Recursive render for nested objects
  const renderRows = (obj: ReportData | ReportData[], parentKey = ""): JSX.Element[] => {
    return Object.entries(obj).flatMap(([key, value]) => {
      const displayKey = parentKey ? `${parentKey} → ${key}` : key;

      if (typeof value === "object" && value !== null) {
        return renderRows(value, displayKey);
      }

      return (
        <div
          key={displayKey}
          className="flex flex-col md:flex-row mb-2 md:mb-3 rounded-lg overflow-hidden shadow-sm"
        >
          {/* Key */}
          <div className="bg-gray-100 px-3 py-2 md:w-1/3 font-semibold text-gray-700 break-words">
            {displayKey}
          </div>
          {/* Value */}
          <div className="bg-white px-3 py-2 md:w-2/3 text-gray-800 break-words">
            {String(value)}
          </div>
        </div>
      );
    });
  };

  

  return (
    <div className="fixed inset-0 flex justify-center items-center bg-black/50 z-60 p-4">
      <div className="bg-white rounded-xl p-6 max-w-3xl w-full relative shadow-lg">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Analysis Report</h3>

        {/* Flex list */}
        <div className="overflow-y-auto max-h-[60vh] space-y-2">{renderRows(emailReport)}</div>

        {/* Copy to Clipboard */}
        <button
          className="mt-4 bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition"
          onClick={() => {
            navigator.clipboard.writeText(JSON.stringify(emailReport, null, 2));
            alert("Report copied to clipboard!");
          }}
        >
          Copy Report
        </button>

        {/* Close modal */}
        <button
          className="absolute top-4 right-4 text-red-500 hover:bg-red-100 p-1 rounded"
          onClick={handleIsOpen}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default Report;
