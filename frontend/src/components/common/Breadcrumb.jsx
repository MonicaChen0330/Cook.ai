import { Link } from 'react-router-dom';
import './Breadcrumb.css';

function Breadcrumb({ paths }) {
    return (
    <nav aria-label="breadcrumb" className="breadcrumb-nav">
        <ol className="breadcrumb-list">
        {paths.map((path, index) => (
            <li key={index} className="breadcrumb-item">
            {path.path ? (
                <Link to={path.path}>{path.name}</Link>
            ) : (
                <span>{path.name}</span>
            )}
            </li>
        ))}
        </ol>
    </nav>
    );
}

export default Breadcrumb;