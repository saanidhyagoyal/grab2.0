package com.gxs.bank.repository;

import com.gxs.bank.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
    List<User> findByRole(User.Role role);
    long countByRole(User.Role role);
    List<User> findByKycStatus(User.KycStatus kycStatus);
    List<User> findByRoleAndKycStatus(User.Role role, User.KycStatus kycStatus);
    long countByKycStatus(User.KycStatus kycStatus);
}
