import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Rediriger automatiquement vers la page Home (pièces)
    navigate('/home', { replace: true });
  }, [navigate]);

  return null;
};

export default Index;