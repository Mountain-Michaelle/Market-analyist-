import * as React from "react"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { FormikProps } from "formik";

interface DataType {
    type: string,
    datas: string[],
    formik: FormikProps<any>
    name: string,
}

export function SelectData({type, name, datas, formik}:DataType) {

  return (
    <Select
    value={formik.values[name]}
    onValueChange={(val) => formik.setFieldValue(name, val)}

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
  )
}
