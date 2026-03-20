import { useParams } from 'react-router-dom';

export default function ResultsPage() {
  const { id } = useParams();
  return <div>Results Page Structure Incoming for {id}</div>;
}
