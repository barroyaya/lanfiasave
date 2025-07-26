import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

const PauvreteChart = ({ data, options }) => {
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    // Si une instance existe déjà, on la détruit
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }
    const ctx = canvasRef.current.getContext('2d');
    chartInstanceRef.current = new Chart(ctx, {
      type: 'bar',
      data: data,
      options: options,
    });

    // Fonction de nettoyage : détruire le graphique au démontage ou re-render
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [data, options]);

  return <canvas id="pauvreteChart" ref={canvasRef} />;
};

export default PauvreteChart;
