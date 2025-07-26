// src/components/ChartComponent.jsx
import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

const ChartComponent = ({ id, type, data, options }) => {
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    // Détruire l'instance existante si elle existe déjà
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }
    const ctx = canvasRef.current.getContext('2d');
    chartInstanceRef.current = new Chart(ctx, {
      type,
      data,
      options,
    });
    // Nettoyage lors du démontage ou mise à jour
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [data, options, type]);

  return <canvas id={id} ref={canvasRef} />;
};

export default ChartComponent;
