import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [EI, setEI] = useState('');
  const [r, setR] = useState('');
  const [g, setG] = useState('');
  const [b, setB] = useState('');
  const [L, setL] = useState('');
  const [a, setA] = useState('');
  const [b2, setB2] = useState('');

  const [imageURL, setImageURL] = useState('');

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('image', file);

    try {
      // Replace 'YOUR_API_ENDPOINT' with the actual API endpoint

      let API_ENDPOINT = 'http://localhost:8000/process'

      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        body: formData,
        mode: 'cors',
      });

      const data = await response.json();
      console.log(data);
      setEI(data.EI); 
      setR(data.r);
      setG(data.g);
      setB(data.b);
      setL(data.l);
      setA(data.a);
      setB2(data.b2);

      if (data.returnImage) {
        //setImageURL(data.returnImage);
        setImageURL(`data:image/jpeg;base64, ${data.returnImage}`)
      }

    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  return (
    <div>
      <h1>Dermi Web</h1>
      <div style={{ maxWidth: '100%' }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload}>Upload</button>
      </div>

      <div id='results'>
        {EI && <p><strong>EI:</strong> {EI}</p>}
        {L && a && b2 && <p>
          <strong>L: </strong>{L}  
          &nbsp;
          <strong> a: </strong>{a} 
          &nbsp;
          <strong> b: </strong>{b2}
        </p>}
        <br></br>
        {r && g && b &&
          <div style={{
            margin: '0 auto',
            backgroundColor: `rgb(${r},${g},${b})`, width: '100px', height: '50px', 
            border: '2px solid black',
            borderRadius: '5px',
          }}>
          </div>
        }
      </div>
      {imageURL &&<img src={imageURL} alt="Result" style={{ maxWidth: '80%' }} />}
    </div>
  );
}

export default App;


