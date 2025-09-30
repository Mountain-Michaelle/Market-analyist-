"use client";
import React, { useState, useEffect, CSSProperties} from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SelectData } from "./select";
import { coins } from "../components/data/coins";
import { timeframes } from "../components/data/timeframe";
import { SendHorizontal } from "lucide-react";
import { ClipLoader } from "react-spinners";
import Report from '../components/report';


// ✅ Define form value types
interface FormValues {
  email: string;
  timeframe: string;
  coin: string;
  description: string;
}

// ✅ Validation schema
const validationSchema: Yup.Schema<FormValues> = Yup.object({
  email: Yup.string()
    .email("Invalid email format")
    .required("Email is required"),
  timeframe: Yup.string().required("Please select a timeframe"),
  coin: Yup.string().required("Please select a coin pair"),
  description: Yup.string()
    .max(300, "Description must be less than 300 characters")
    .required("Description is required"),
});

const Submission: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stageMessage, setStageMessage] = useState<string | null>(null);
  const [emailReport, setEmailReport] = useState<any>()
  const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
    document.body.style.overflow = stageMessage ? "hidden" : "auto";
  }, [stageMessage]);

  const handleIsOpen = () => {
    setIsOpen(!isOpen)
    console.log("isOpen", isOpen)
  }

  console.log("data, emailreport", emailReport)
  const override: CSSProperties = {
  display: "block",
  margin: "0 auto",
  borderTopColor: "blue",
  borderRightColor: "rgb(255 255 255 / 39%)",
  borderBottomColor: "#0000ff40 ",
  borderLeftColor: "#0034ff33"
}

  const formik = useFormik<FormValues>({
    initialValues: {
      email: "",
      timeframe: "",
      coin: "",
      description: "",
    },
    validationSchema,
    onSubmit: async (values, {resetForm }) => {
      setLoading(true);
      setStageMessage("⏳ Submitting request...");

      try {
        // ✅ Call backend API
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_LINK}/api/analyze/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(values),
        });

        const data = await response.json();

        if (response.ok) {
          const taskId = data.task_id; // ✅ use Celery task_id instead of DB id
          setStageMessage("✅ Request queued. Waiting for updates...");

          // Poll the status endpoint every 2s
          const interval = setInterval(async () => {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_LINK}/api/status/${taskId}/`);
            const statusData = await res.json();

            // show progress step if provided
            if (statusData.progress?.step) {
              setStageMessage(`⏳ ${statusData.progress.step}`);
            }

            // check celery state
            // check celery state
            if (statusData.celery_state === "SUCCESS") {
              clearInterval(interval);
              
              // ✅ Check for email warning
              if (statusData.email_status && !statusData.email_status.success) {
                setStageMessage(
                  `✅ Analysis complete! ⚠️ Email not sent: ${statusData.email_status.error}`
                );
                console.log(statusData.email_status.error, "Status data")
              } else {
                setStageMessage(!statusData.result.email_status?.error ?
                  "✅Analysis complete! Email sent successfully": "✅Analysis complete! ⚠️Email not sent, recheck your email and try again");
              }

              console.log("Final result:", statusData.result.email_status);
              setEmailReport(statusData.result)
            } else if (statusData.celery_state === "FAILURE") {
              clearInterval(interval);
              setStageMessage("❌ Task failed.");
            }

          }, 2000);
        } else {
          setStageMessage("❌ Error: " + JSON.stringify(data));
        }
      } catch (error) {
        console.error("Request failed:", error);
        setStageMessage("⚠️ Something went wrong. Please try again.");
      } finally {
        setLoading(false);
      }
    },
  });

  return (
    <div className="mt-8 flex justify-center">
      <form
        onSubmit={formik.handleSubmit}
        className="flex flex-col m-10 md:m-0 w-full max-w-3xl"
      >
        {/* Row of Email + Timeframe + Coin */}
        <div className="flex flex-col md:flex-row justify-center w-full gap-3">
          <div className="flex flex-col w-full md:w-1/2">
            <label>Email</label>
            <Input
              type="text"
              placeholder="Your email"
              {...formik.getFieldProps("email")}
            />
            {formik.touched.email && formik.errors.email && (
              <p className="text-red-400 text-sm">{formik.errors.email}</p>
            )}
          </div>

          <div className="flex flex-col w-full md:w-1/2">
            <label>Timeframe/hr</label>
            <SelectData
              datas={timeframes}
              type="Timeframes"
              formik={formik}
              name="timeframe"
            />
            {formik.touched.timeframe && formik.errors.timeframe && (
              <p className="text-red-400 text-sm">{formik.errors.timeframe}</p>
            )}
          </div>

          <div className="flex flex-col md:w-1/2">
            <label>Coin pair</label>
            <SelectData
              datas={coins}
              type="Crypto coins"
              name="coin"
              formik={formik}
            />
            {formik.touched.coin && formik.errors.coin && (
              <p className="text-red-400 text-sm">{formik.errors.coin}</p>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="mt-5 flex flex-col gap-2">
          <Textarea
            placeholder="Brief description"
            className="resize-none max-h-20"
            {...formik.getFieldProps("description")}
          />
          {formik.touched.description && formik.errors.description && (
            <p className="text-red-400 text-sm">{formik.errors.description}</p>
          )}
        </div>

        {/* Submit */}
        <div className="flex w-full justify-center mt-10">
          <button
            type="submit"
            className="border p-2 pl-5 pr-5 flex items-center gap-2"
            disabled={loading}
          >
            <SendHorizontal className="text-2xl cursor-pointer text-gray-500 w-6 h-6" />
            {loading ?  <ClipLoader
                color={"green"}
                speedMultiplier={0.5}
                loading={true}
                cssOverride={override}
                size={50}
                aria-label="Loading Spinner"
                data-testid="loader"
              /> : "Submit"}
          </button>
        </div>
      </form>

      {/* ✅ Stage messages */}
      {stageMessage && (
        <div className="fixed left-0 -top-5 flex flex-1 justify-center items-center
         bg-white/90 inset-0 w-full h-[100%]  z-9999 mt-5 text-center text-blue-600 font-medium">
        
      <div className="flex justify-center items-center w-full h-20">
        <p className={` relative z-10 text-blue-800 font-medium px-4 py-2 
                    transition-all duration-700 ease-out translate-y-2 
                    ${stageMessage?.toLowerCase().includes("complete") ? '' : 'animate-bounce'}
                    ${stageMessage?.toLowerCase().includes("not") && 'text-pink-500'}
                    ${stageMessage === '✅Analysis complete! Email sent successfully.' && 'text-green-500'}
                    `}
        >
          <span className="relative">
            {stageMessage}
            <span
            
              className="absolute -left-30 inset-0 
                        bg-white blur-[15px] rounded-full w-[150%] md:w-[200%]
                        z-10"
            ></span>
          </span>
        </p>
      
      </div>

       {
        stageMessage?.toLowerCase().includes("complete") ? (
        <>
          <Report emailReport={emailReport} isOpen={isOpen} handleIsOpen={handleIsOpen} />
          <button className='absolute top-2/3 cursor-pointer text-green-500 border p-2 pl-4 pr-4 rounded-sm  
           '
           onClick={() => handleIsOpen()}
           >View Report</button>
        </>
        ) :
        ('')
        
      }
      
      {
        stageMessage !== '' ?
        <button className='absolute top-1/10 right-1/12 cursor-pointer text-red-500 border p-2 pl-4 pr-4 rounded-sm  
           '
           onClick={() => setStageMessage('')}
           >Close</button>
           :

           ''
      }
          
        </div>
      )}
    </div>
  );
};

export default Submission;
