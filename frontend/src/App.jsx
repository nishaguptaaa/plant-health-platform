import { useEffect, useState } from "react";

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
    return <p>Could not load plants: {error}</p>;
  }

  return (
    <div>
      <h1>My Plants</h1>
      <ul>
        {plants.map((plant) => (
          <li key={plant.id}>
            {plant.nickname ?? plant.plant_code} — {plant.common_name ?? "Unidentified species"}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
