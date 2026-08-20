'use client';

import { useState } from 'react';
import CityMesh from '@/components/map/CityMesh';

export default function MapPage() {
  const [selectedCity, setSelectedCity] = useState('mumbai');

  return (
    <div className="h-full w-full">
      <CityMesh selectedCity={selectedCity} onCityChange={setSelectedCity} />
    </div>
  );
}
