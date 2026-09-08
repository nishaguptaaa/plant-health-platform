import { useEffect, useState } from "react";
import "./App.css";

function locationLabel(plant) {
  if (!plant.zone_name) {
    return "Not yet placed";
  }
  return [plant.space_name, plant.zone_name].filter(Boolean).join(", ");
}

function PlantCard({ plant }) {
  return (
    <div className="plant-card">
      <div className="plant-card-accent" />
      <h3 className="plant-card-name">
        {plant.nickname ?? plant.plant_code}
      </h3>
      <p className="plant-card-species">
        {plant.common_name ?? "Unidentified species"}
      </p>
      <p className="plant-card-location">{locationLabel(plant)}</p>
    </div>
  );
}

function App() {
  const [plants, setPlants] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/plants")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setPlants(data))
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <main className="page">
        <p>Could not load plants: {error}</p>
      </main>
    );
  }

  return (
    <main className="page">
      <h1>My Plants</h1>
      <div className="plant-grid">
        {plants.map((plant) => (
          <PlantCard key={plant.id} plant={plant} />
        ))}
      </div>
    </main>
  );
}

export default App;
