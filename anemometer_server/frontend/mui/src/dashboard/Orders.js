import * as React from 'react';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Title from './Title';

import { useEffect,useState } from 'react';
//import { adaptEventHandlers } from 'recharts/types/util/types';

// Generate Order Data

function formatTime(isoTimeString) {
  const date = new Date(isoTimeString);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

function preventDefault(event) {
  event.preventDefault();
}


export default function Orders() {
  const [Adatas,setAdatas]=useState([]);


  function fetchdata(){
    console.log("orders fetch data");
    fetch("http://localhost:8000/seri/anemometor/")
      .then((res)=>res.json())
      .then(json=>{
        setAdatas(json);
        console.log(json);
      })
      .catch((error)=>console.log(error));
  }

  useEffect(()=>{
    const intervalID=setInterval(fetchdata,1000);
    return ()=>{
      clearInterval(intervalID);
    }
  })

  return (
    <React.Fragment>
      <Title>Each Anemometer</Title>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Time</TableCell>
            <TableCell>Speed</TableCell>
            <TableCell>Direction</TableCell>
            <TableCell>point</TableCell>
            <TableCell>State</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Adatas.map((Adata) => (
            <TableRow key={Adata.AID}>
              <TableCell>{formatTime(Adata.LastUpdate)}</TableCell>
              <TableCell>9.5 m/s</TableCell>
              <TableCell> -- </TableCell>
              <TableCell> -- </TableCell>
              <TableCell>{Adata.Status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </React.Fragment>
  );
}