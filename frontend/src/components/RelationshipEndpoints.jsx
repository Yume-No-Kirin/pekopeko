export default function RelationshipEndpoints({ endpoints }) {
  return (
    <ul className="relationship-endpoints">
      {endpoints.map(({ id, label }, index) => (
        <li key={`${id}-${index}`}>{label ? label : <code>{id}</code>}</li>
      ))}
    </ul>
  );
}
