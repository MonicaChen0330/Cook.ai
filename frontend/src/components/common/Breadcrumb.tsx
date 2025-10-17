import { Link } from 'react-router-dom';

interface BreadcrumbPath {
  name: string;
  path?: string;
}

interface BreadcrumbProps {
  paths: BreadcrumbPath[];
}

function Breadcrumb({ paths }: BreadcrumbProps) {
  return (
    <nav className="mb-0">
      <ol className="list-none p-0 m-0 flex items-center gap-2 text-sm">
        {paths.map((path, index) => (
          <li key={index} className="flex items-center">
            {path.path ? (
              <Link to={path.path} className="text-blue-500 no-underline transition-colors hover:underline">
                {path.name}
              </Link>
            ) : (
              <span className="text-gray-600">{path.name}</span>
            )}
            {index < paths.length - 1 && (
              <span className="ml-2 text-gray-400">/</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default Breadcrumb;