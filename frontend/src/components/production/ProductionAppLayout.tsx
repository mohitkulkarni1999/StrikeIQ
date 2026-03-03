/**
 * Production App Layout for StrikeIQ
 * Implements stable authentication flow without redirect loops
 */

import React from 'react';
import AppBootstrapGuard from './AppBootstrapGuard';
import RouteGuard from './RouteGuard';

interface ProductionAppLayoutProps {
  children: React.ReactNode;
}

const ProductionAppLayout: React.FC<ProductionAppLayoutProps> = ({ children }) => {
  return (
    <AppBootstrapGuard>
      <RouteGuard>
        {children}
      </RouteGuard>
    </AppBootstrapGuard>
  );
};

export default ProductionAppLayout;
