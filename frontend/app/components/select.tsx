import * as React from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FormikProps } from "formik";

// Generic form values type
interface FormValues {
  [key: string]: string;
}

// Props for SelectData
interface DataType<T> {
  type: string;
  datas: string[];
  formik: FormikProps<T>;
  name: keyof T; // name must be a valid key of the form values
}

export function SelectData<T>({ type, name, datas, formik }: DataType<T>) {
  return (
    <Select
      value={formik.values[name] as unknown as string} // safe assertion
      onValueChange={(val: string) => formik.setFieldValue(name as string, val)}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>{type}</SelectLabel>
          {datas.map((data) => (
            <SelectItem key={data.toLowerCase()} value={data}>
              {data}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
