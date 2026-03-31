package com.gxs.bank.seed;

import com.gxs.bank.model.Promotion;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.PromotionRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.LocalDate;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PromotionRepository promotionRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        seedUsers();
        seedPromotions();
        log.info("✅ Database seeded successfully");
    }

    private void seedUsers() {
        if (userRepository.count() > 0) return;

        // Demo Customer
        userRepository.save(User.builder()
                .fullName("Alex Chen")
                .email("alex@demo.com")
                .phone("+6591234567")
                .passwordHash(passwordEncoder.encode("demo1234"))
                .role(User.Role.CUSTOMER)
                .build());

        // Demo Employee
        userRepository.save(User.builder()
                .fullName("Sarah Tan")
                .email("sarah@gxs.com.sg")
                .phone("+6598765432")
                .passwordHash(passwordEncoder.encode("admin1234"))
                .role(User.Role.EMPLOYEE)
                .employeeId("GXS-EMP-001")
                .department("Customer Service")
                .build());

        log.info("👤 Seeded demo users (alex@demo.com / demo1234, sarah@gxs.com.sg / admin1234)");
    }

    private void seedPromotions() {
        if (promotionRepository.count() > 0) return;

        promotionRepository.save(Promotion.builder()
                .title("For the aiyah moments in life")
                .description("Plot twist, no problem! Get fast cash at our lowest rates from 1.08% p.a. (EIR 2.02% p.a.), with no fees and interest rebate of 1.8% in cashback.")
                .badgeText("FlexiLoan")
                .ctaText("Apply now")
                .ctaUrl("/loans")
                .termsUrl("/terms/aiyah")
                .validFrom(LocalDate.of(2026, 1, 19))
                .validTo(LocalDate.of(2026, 3, 31))
                .isActive(true)
                .build());

        promotionRepository.save(Promotion.builder()
                .title("Daily interest. Daily rewards.")
                .description("See your money grow with daily interest credited to your account. Earn up to 2.08% p.a. on your savings.")
                .badgeText("Savings")
                .ctaText("GXS Savings Account")
                .ctaUrl("/savings")
                .validFrom(LocalDate.of(2026, 1, 1))
                .validTo(LocalDate.of(2026, 12, 31))
                .isActive(true)
                .build());

        promotionRepository.save(Promotion.builder()
                .title("The starter credit card.")
                .description("A no-interest credit card with unlimited instant rewards and no minimum income requirement.")
                .badgeText("FlexiCard")
                .ctaText("GXS FlexiCard")
                .ctaUrl("/cards")
                .validFrom(LocalDate.of(2026, 1, 1))
                .validTo(LocalDate.of(2026, 12, 31))
                .isActive(true)
                .build());

        promotionRepository.save(Promotion.builder()
                .title("Instant cash with GXS FlexiLoan")
                .description("Get an instant cash boost with GXS FlexiLoan. Enjoy 0% interest rate with Balance transfer or no additional fees with our Instalment loan.")
                .badgeText("Loans")
                .ctaText("GXS FlexiLoan")
                .ctaUrl("/loans")
                .validFrom(LocalDate.of(2026, 1, 1))
                .validTo(LocalDate.of(2026, 12, 31))
                .isActive(true)
                .build());

        log.info("🎯 Seeded {} promotions", 4);
    }
}
